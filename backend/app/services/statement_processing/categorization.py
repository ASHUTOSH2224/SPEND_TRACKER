import re
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.queries.statement_processing import (
    find_assignable_category_id_by_name,
    find_merchant_history_match,
    list_active_rules_for_user,
)
from app.schemas.rules import RuleMatchType
from app.services.statement_processing.llm import NoOpLLMCategoryProvider
from app.services.statement_processing.types import (
    CategorizationDecision,
    LLMCategoryProvider,
    NormalizedTransactionRow,
    TransactionCategorizer,
)

RULE_MATCH_CONFIDENCE = Decimal("0.9500")
CHARGE_MATCH_CONFIDENCE = Decimal("0.9900")

_CHARGE_CATEGORY_NAME_BY_TYPE = {
    "annual_fee": "Annual Fee",
    "joining_fee": "Joining Fee",
    "late_fee": "Late Fee",
    "finance_charge": "Finance Charge",
    "emi_processing_fee": "EMI Processing Fee",
    "cash_advance_fee": "Cash Advance Fee",
    "forex_markup": "Forex Markup",
    "tax": "Tax on Charge",
}


class DeterministicRuleCategorizer:
    def __init__(self, session: Session) -> None:
        self._session = session

    def categorize(
        self,
        *,
        user_id: UUID,
        normalized_row: NormalizedTransactionRow,
    ) -> CategorizationDecision | None:
        charge_decision = self._match_charge_category(
            user_id=user_id,
            normalized_row=normalized_row,
        )
        if charge_decision is not None:
            return charge_decision

        rules = list_active_rules_for_user(self._session, user_id=user_id)
        for rule in rules:
            if _rule_matches(
                match_type=rule.match_type,
                match_value=rule.match_value,
                normalized_row=normalized_row,
            ):
                return CategorizationDecision(
                    category_id=rule.assigned_category_id,
                    category_source="rule",
                    category_confidence=RULE_MATCH_CONFIDENCE,
                    category_explanation=f"Matched rule '{rule.rule_name}'",
                    review_required=False,
                )
        return None

    def _match_charge_category(
        self,
        *,
        user_id: UUID,
        normalized_row: NormalizedTransactionRow,
    ) -> CategorizationDecision | None:
        if not normalized_row.is_card_charge or normalized_row.charge_type is None:
            return None

        category_name = _CHARGE_CATEGORY_NAME_BY_TYPE.get(normalized_row.charge_type)
        if category_name is None:
            return None

        category_id = find_assignable_category_id_by_name(
            self._session,
            user_id=user_id,
            category_name=category_name,
        )
        return CategorizationDecision(
            category_id=category_id,
            category_source="rule" if category_id is not None else None,
            category_confidence=CHARGE_MATCH_CONFIDENCE if category_id is not None else None,
            category_explanation=(
                f"Matched charge keyword for {normalized_row.charge_type.replace('_', ' ')}"
                if category_id is not None
                else None
            ),
            review_required=category_id is None,
        )


class MerchantHistoryCategorizer:
    def __init__(self, session: Session) -> None:
        self._session = session

    def categorize(
        self,
        *,
        user_id: UUID,
        normalized_row: NormalizedTransactionRow,
    ) -> CategorizationDecision | None:
        match = find_merchant_history_match(
            self._session,
            user_id=user_id,
            normalized_merchant=normalized_row.normalized_merchant,
        )
        if match is None:
            return None

        return CategorizationDecision(
            category_id=match.category_id,
            category_source="history",
            category_confidence=Decimal(str(match.confidence)).quantize(
                Decimal("0.0001")
            ),
            category_explanation=(
                "Matched merchant history "
                f"using {match.supporting_transaction_count} prior transaction(s)"
            ),
            review_required=False,
        )


class HybridTransactionCategorizer(TransactionCategorizer):
    def __init__(
        self,
        session: Session,
        *,
        llm_provider: LLMCategoryProvider | None = None,
    ) -> None:
        self._deterministic = DeterministicRuleCategorizer(session)
        self._history = MerchantHistoryCategorizer(session)
        self._llm_provider = llm_provider or NoOpLLMCategoryProvider()

    def categorize(
        self,
        *,
        user_id: UUID,
        normalized_row: NormalizedTransactionRow,
    ) -> CategorizationDecision:
        deterministic_decision = self._deterministic.categorize(
            user_id=user_id,
            normalized_row=normalized_row,
        )
        if deterministic_decision is not None:
            return deterministic_decision

        history_decision = self._history.categorize(
            user_id=user_id,
            normalized_row=normalized_row,
        )
        if history_decision is not None:
            return history_decision

        llm_decision = self._llm_provider.categorize(
            user_id=user_id,
            normalized_row=normalized_row,
        )
        if llm_decision is not None:
            return llm_decision

        return CategorizationDecision(
            category_id=None,
            category_source=None,
            category_confidence=None,
            category_explanation="No deterministic or history categorization match",
            review_required=True,
        )


def _rule_matches(
    *,
    match_type: RuleMatchType | str,
    match_value: str,
    normalized_row: NormalizedTransactionRow,
) -> bool:
    lowered_match_value = match_value.strip().lower()
    description = normalized_row.raw_description.lower()
    merchant = normalized_row.normalized_merchant.lower()

    if match_type == "description_contains":
        return lowered_match_value in description
    if match_type == "merchant_equals":
        return merchant == lowered_match_value
    if match_type == "regex":
        try:
            return (
                re.search(
                    match_value,
                    normalized_row.raw_description,
                    flags=re.IGNORECASE,
                )
                is not None
            )
        except re.error:
            return False
    return False

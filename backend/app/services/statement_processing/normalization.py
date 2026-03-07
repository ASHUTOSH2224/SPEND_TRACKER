import hashlib
import re
from decimal import Decimal

from app.models.statement import Statement
from app.services.statement_processing.types import (
    NormalizedTransactionRow,
    ParsedStatementResult,
    ParsedTransactionRow,
    StatementNormalizer,
)

_WHITESPACE_PATTERN = re.compile(r"\s+")
_MERCHANT_CLEAN_PATTERN = re.compile(r"[^a-z0-9 ]+")

_CHARGE_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("annual_fee", ("annual fee",)),
    ("joining_fee", ("joining fee", "membership fee")),
    ("late_fee", ("late fee", "overdue fee")),
    ("finance_charge", ("finance charge", "interest charge")),
    ("emi_processing_fee", ("emi processing fee",)),
    ("cash_advance_fee", ("cash advance fee",)),
    ("forex_markup", ("forex markup", "markup fee")),
    ("tax", ("gst", "tax on charge")),
)


def _collapse_whitespace(value: str) -> str:
    return _WHITESPACE_PATTERN.sub(" ", value.strip())


def _normalize_merchant(row: ParsedTransactionRow) -> str:
    merchant = _collapse_whitespace(row.merchant or row.description)
    merchant = _MERCHANT_CLEAN_PATTERN.sub(" ", merchant.lower())
    merchant = _collapse_whitespace(merchant)
    return merchant.title() if merchant else "Unknown Merchant"


def _detect_charge_type(description: str) -> str | None:
    lowered = description.lower()
    for charge_type, keywords in _CHARGE_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return charge_type
    return None


def _build_source_hash(
    *,
    statement: Statement,
    row: ParsedTransactionRow,
    normalized_merchant: str,
) -> str:
    digest = hashlib.sha256()
    digest.update(str(statement.user_id).encode("utf-8"))
    digest.update(b"|")
    digest.update(str(statement.card_id).encode("utf-8"))
    digest.update(b"|")
    digest.update(row.txn_date.isoformat().encode("utf-8"))
    digest.update(b"|")
    digest.update(str(row.amount).encode("utf-8"))
    digest.update(b"|")
    digest.update(row.txn_direction.encode("utf-8"))
    digest.update(b"|")
    digest.update(normalized_merchant.lower().encode("utf-8"))
    digest.update(b"|")
    digest.update(_collapse_whitespace(row.description).lower().encode("utf-8"))
    return digest.hexdigest()


class DefaultStatementNormalizer(StatementNormalizer):
    def normalize(
        self,
        *,
        statement: Statement,
        parsed_statement: ParsedStatementResult,
    ) -> list[NormalizedTransactionRow]:
        normalized_rows: list[NormalizedTransactionRow] = []
        for row in parsed_statement.rows:
            description = _collapse_whitespace(row.description)
            normalized_merchant = _normalize_merchant(row)
            charge_type = _detect_charge_type(description)
            is_card_charge = charge_type is not None

            txn_type = "spend"
            if row.txn_direction == "credit":
                txn_type = "refund"
            elif is_card_charge:
                txn_type = "charge"

            metadata_json = {
                "parser_name": parsed_statement.parser_name,
                "raw_metadata": row.metadata,
            }

            normalized_rows.append(
                NormalizedTransactionRow(
                    txn_date=row.txn_date,
                    posted_date=row.posted_date,
                    raw_description=description,
                    normalized_merchant=normalized_merchant,
                    amount=abs(Decimal(row.amount)),
                    currency=row.currency,
                    txn_direction=row.txn_direction,
                    txn_type=txn_type,
                    is_card_charge=is_card_charge,
                    charge_type=charge_type,
                    is_reward_related=False,
                    reward_points_delta=None,
                    cashback_amount=None,
                    source_hash=_build_source_hash(
                        statement=statement,
                        row=row,
                        normalized_merchant=normalized_merchant,
                    ),
                    metadata_json=metadata_json,
                )
            )
        return normalized_rows

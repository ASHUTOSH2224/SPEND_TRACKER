from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID

from app.models.statement import Statement


@dataclass(frozen=True, slots=True)
class ParsedTransactionRow:
    txn_date: date
    description: str
    amount: Decimal
    posted_date: date | None = None
    merchant: str | None = None
    currency: str = "INR"
    txn_direction: str = "debit"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ParsedStatementResult:
    parser_name: str
    rows: list[ParsedTransactionRow]


@dataclass(frozen=True, slots=True)
class StatementFilePayload:
    file_storage_key: str
    file_name: str
    content_bytes: bytes
    password: str | None = field(default=None, repr=False)


@dataclass(frozen=True, slots=True)
class NormalizedTransactionRow:
    txn_date: date
    raw_description: str
    normalized_merchant: str
    amount: Decimal
    source_hash: str
    posted_date: date | None = None
    currency: str = "INR"
    txn_direction: str = "debit"
    txn_type: str = "spend"
    is_card_charge: bool = False
    charge_type: str | None = None
    is_reward_related: bool = False
    reward_points_delta: Decimal | None = None
    cashback_amount: Decimal | None = None
    metadata_json: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class CategorizationDecision:
    category_id: UUID | None
    category_source: str | None
    category_confidence: Decimal | None
    category_explanation: str | None
    review_required: bool


class StatementParser(Protocol):
    def parse(
        self,
        *,
        statement: Statement,
        statement_file: StatementFilePayload,
    ) -> ParsedStatementResult:
        ...


class StatementNormalizer(Protocol):
    def normalize(
        self,
        *,
        statement: Statement,
        parsed_statement: ParsedStatementResult,
    ) -> list[NormalizedTransactionRow]:
        ...


class TransactionCategorizer(Protocol):
    def categorize(
        self,
        *,
        user_id: UUID,
        normalized_row: NormalizedTransactionRow,
    ) -> CategorizationDecision:
        ...


class LLMCategoryProvider(Protocol):
    def categorize(
        self,
        *,
        user_id: UUID,
        normalized_row: NormalizedTransactionRow,
    ) -> CategorizationDecision | None:
        ...

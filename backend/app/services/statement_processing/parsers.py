import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import StringIO

from app.models.statement import Statement
from app.services.statement_processing.types import (
    ParsedStatementResult,
    ParsedTransactionRow,
    StatementFilePayload,
    StatementParser,
)

_HEADER_ALIASES = {
    "transaction_date": ("transaction date",),
    "posted_date": ("post date", "posted date"),
    "description": ("description",),
    "debit": ("debit", "debit amount"),
    "credit": ("credit", "credit amount"),
    "currency": ("currency",),
    "merchant": ("merchant", "merchant name"),
}


def select_statement_parser(
    *,
    statement: Statement,
    issuer_name: str,
) -> StatementParser:
    if statement.file_type == "csv" and issuer_name.strip().casefold() == "hdfc":
        return HDFCCreditCardCsvStatementParser()
    return NoOpStatementParser()


class HDFCCreditCardCsvStatementParser(StatementParser):
    parser_name = "hdfc_credit_card_csv_v1"

    def parse(
        self,
        *,
        statement: Statement,
        statement_file: StatementFilePayload,
    ) -> ParsedStatementResult:
        del statement

        try:
            file_text = statement_file.content_bytes.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("Unsupported HDFC CSV encoding; expected UTF-8") from exc

        reader = csv.DictReader(StringIO(file_text))
        if not reader.fieldnames:
            raise ValueError("Unsupported HDFC CSV format: missing header row")

        header_map = _build_header_map(reader.fieldnames)
        rows: list[ParsedTransactionRow] = []
        for line_number, raw_row in enumerate(reader, start=2):
            if _is_empty_csv_row(raw_row):
                continue

            try:
                txn_date = _parse_date(
                    _get_required_value(raw_row, header_map, "transaction_date")
                )
                posted_date_value = _get_optional_value(raw_row, header_map, "posted_date")
                posted_date = (
                    _parse_date(posted_date_value) if posted_date_value else None
                )
                description = _get_required_value(raw_row, header_map, "description")
                debit_amount = _parse_optional_amount(
                    _get_optional_value(raw_row, header_map, "debit")
                )
                credit_amount = _parse_optional_amount(
                    _get_optional_value(raw_row, header_map, "credit")
                )
                txn_direction, amount = _resolve_direction_and_amount(
                    debit_amount=debit_amount,
                    credit_amount=credit_amount,
                )
            except ValueError as exc:
                raise ValueError(f"Invalid HDFC CSV row {line_number}: {exc}") from exc

            rows.append(
                ParsedTransactionRow(
                    txn_date=txn_date,
                    posted_date=posted_date,
                    description=description,
                    merchant=_get_optional_value(raw_row, header_map, "merchant"),
                    amount=amount,
                    currency=_get_optional_value(raw_row, header_map, "currency") or "INR",
                    txn_direction=txn_direction,
                    metadata={
                        "line_number": line_number,
                        "raw_row": {
                            key: (value.strip() if isinstance(value, str) else value)
                            for key, value in raw_row.items()
                        },
                    },
                )
            )

        return ParsedStatementResult(
            parser_name=self.parser_name,
            rows=rows,
        )


class NoOpStatementParser(StatementParser):
    """Placeholder parser used until issuer-specific parsers are implemented."""

    def parse(
        self,
        *,
        statement: Statement,
        statement_file: StatementFilePayload,
    ) -> ParsedStatementResult:
        del statement, statement_file
        return ParsedStatementResult(
            parser_name="noop",
            rows=[],
        )


def _build_header_map(fieldnames: list[str]) -> dict[str, str]:
    normalized_to_actual = {
        _normalize_header_name(fieldname): fieldname
        for fieldname in fieldnames
        if fieldname
    }
    header_map: dict[str, str] = {}
    missing_headers: list[str] = []
    for canonical_name, aliases in _HEADER_ALIASES.items():
        matched_header = next(
            (
                normalized_to_actual[alias]
                for alias in aliases
                if alias in normalized_to_actual
            ),
            None,
        )
        if matched_header is None:
            if canonical_name in {"currency", "merchant"}:
                continue
            missing_headers.append(canonical_name)
            continue
        header_map[canonical_name] = matched_header

    if missing_headers:
        missing_display = ", ".join(sorted(missing_headers))
        raise ValueError(
            "Unsupported HDFC CSV format: missing required columns "
            f"{missing_display}"
        )
    return header_map


def _normalize_header_name(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").split())


def _get_required_value(
    row: dict[str, str | None],
    header_map: dict[str, str],
    canonical_name: str,
) -> str:
    actual_name = header_map[canonical_name]
    value = row.get(actual_name)
    if value is None or not value.strip():
        raise ValueError(f"{canonical_name} is required")
    return value.strip()


def _get_optional_value(
    row: dict[str, str | None],
    header_map: dict[str, str],
    canonical_name: str,
) -> str | None:
    actual_name = header_map.get(canonical_name)
    if actual_name is None:
        return None
    value = row.get(actual_name)
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _parse_date(value: str) -> date:
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError("unsupported date format")


def _parse_optional_amount(value: str | None) -> Decimal | None:
    if value is None:
        return None
    normalized = value.replace(",", "").strip()
    if not normalized:
        return None
    try:
        return abs(Decimal(normalized))
    except InvalidOperation as exc:
        raise ValueError("invalid amount") from exc


def _resolve_direction_and_amount(
    *,
    debit_amount: Decimal | None,
    credit_amount: Decimal | None,
) -> tuple[str, Decimal]:
    if debit_amount is not None and credit_amount is not None:
        raise ValueError("expected only one of debit or credit amount")
    if debit_amount is None and credit_amount is None:
        raise ValueError("missing debit or credit amount")
    if debit_amount is not None:
        return "debit", debit_amount
    assert credit_amount is not None
    return "credit", credit_amount


def _is_empty_csv_row(row: dict[str, str | None]) -> bool:
    return all(value is None or not value.strip() for value in row.values())

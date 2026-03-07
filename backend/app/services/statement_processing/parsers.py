from app.models.statement import Statement
from app.services.statement_processing.types import ParsedStatementResult, StatementParser


class NoOpStatementParser(StatementParser):
    """Placeholder parser used until issuer-specific parsers are implemented."""

    def parse(self, *, statement: Statement) -> ParsedStatementResult:
        return ParsedStatementResult(
            parser_name="noop",
            rows=[],
        )

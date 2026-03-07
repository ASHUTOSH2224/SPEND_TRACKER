from app.core.config import get_settings
from app.services.statement_processing.types import CategorizationDecision, LLMCategoryProvider, NormalizedTransactionRow


class NoOpLLMCategoryProvider(LLMCategoryProvider):
    """Replaceable LLM provider stub. Real model calls are intentionally deferred."""

    def categorize(
        self,
        *,
        user_id,
        normalized_row: NormalizedTransactionRow,
    ) -> CategorizationDecision | None:
        return None


def get_llm_category_provider() -> LLMCategoryProvider:
    settings = get_settings()
    if settings.llm_provider_backend == "noop":
        return NoOpLLMCategoryProvider()
    return NoOpLLMCategoryProvider()

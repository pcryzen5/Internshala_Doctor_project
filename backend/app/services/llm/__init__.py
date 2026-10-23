"""LLM provider package and factory."""

from app.core.config import settings
from app.services.llm.anthropic import AnthropicLLMProvider
from app.services.llm.base import LLMProvider
from app.services.llm.mock import MockLLMProvider


def get_llm_provider() -> LLMProvider:
    """Factory creating the active LLM provider based on application settings."""
    if settings.LLM_PROVIDER == "anthropic" and settings.ANTHROPIC_API_KEY:
        return AnthropicLLMProvider(
            api_key=settings.ANTHROPIC_API_KEY,
            model=settings.LLM_MODEL,
        )
    return MockLLMProvider()

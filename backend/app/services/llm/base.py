"""Abstract base class for LLM extraction providers."""

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract provider for LLM structured clinical extraction."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name/version of the underlying LLM model."""
        pass

    @abstractmethod
    async def extract_clinical_summary(
        self,
        transcript: str,
        system_prompt: str,
        error_feedback: str | None = None,
    ) -> dict[str, Any]:
        """Calls the LLM provider and returns raw parsed dict conforming to ClinicalSummary."""
        pass

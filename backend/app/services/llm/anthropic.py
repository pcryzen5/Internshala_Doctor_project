"""Anthropic Claude LLM provider implementing structured clinical extraction."""

import json
import logging
from typing import Any

from app.core.config import settings
from app.core.errors import LLMFailedError
from app.schemas.clinical_summary import ClinicalSummary
from app.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class AnthropicLLMProvider(LLMProvider):
    """Anthropic Claude provider using tool-use for guaranteed JSON schema conformance."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.LLM_MODEL or "claude-3-5-sonnet-20241022"

    @property
    def model_name(self) -> str:
        return self.model

    async def extract_clinical_summary(
        self,
        transcript: str,
        system_prompt: str,
        error_feedback: str | None = None,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise LLMFailedError("ANTHROPIC_API_KEY is not configured")

        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=self.api_key)

            # Define tool schema from ClinicalSummary Pydantic model
            tool_schema = ClinicalSummary.model_json_schema()

            tools = [
                {
                    "name": "record_clinical_summary",
                    "description": (
                        "Extract factual clinical information into the structured "
                        "medical record schema."
                    ),
                    "input_schema": tool_schema,
                }
            ]

            user_content = (
                f"Consultation transcript to extract:\n\n<transcript>\n{transcript}\n</transcript>"
            )
            if error_feedback:
                user_content += (
                    f"\n\nNOTE: A previous extraction attempt failed with this validation error: "
                    f"{error_feedback}. Please correct your output to strictly satisfy the schema."
                )

            messages_client: Any = client.messages
            response = await messages_client.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.0,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
                tools=tools,
                tool_choice={"type": "tool", "name": "record_clinical_summary"},
            )

            # Extract tool use call
            for content_block in response.content:
                if (
                    content_block.type == "tool_use"
                    and content_block.name == "record_clinical_summary"
                ):
                    if isinstance(content_block.input, dict):
                        return content_block.input
                    if isinstance(content_block.input, str):
                        return json.loads(content_block.input)  # type: ignore[no-any-return]

            raise LLMFailedError("Anthropic did not invoke the record_clinical_summary tool")

        except Exception as exc:
            logger.error("Anthropic API extraction error: %s", str(exc))
            raise LLMFailedError(f"LLM extraction failed: {exc}") from exc

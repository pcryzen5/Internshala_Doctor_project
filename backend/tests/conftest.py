"""Global pytest test configuration and fixtures."""

from collections.abc import Generator

import numpy as np
import pytest

from app.api.deps import get_asr_service
from app.main import app
from app.services.asr import ASRService, TranscribeResult


class MockASRService(ASRService):
    """Hermetic fast mock for ASR in test environments."""

    async def transcribe(
        self, audio_array: np.ndarray, sample_rate: int = 16000
    ) -> TranscribeResult:
        return TranscribeResult(
            text="I have had fever since two days",
            start_ms=100,
            end_ms=1500,
            confidence=0.94,
            is_hallucination=False,
        )


@pytest.fixture(autouse=True)
def override_asr() -> Generator[None, None, None]:
    """Globally mock ASR in integration tests to ensure deterministic sub-second test execution."""
    app.dependency_overrides[get_asr_service] = lambda: MockASRService()
    yield
    app.dependency_overrides.clear()

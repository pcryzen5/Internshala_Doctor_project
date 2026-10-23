"""Tests for ASR service and hallucination filter."""

import io
import wave

import numpy as np
import pytest

from app.services.asr import ASRService, HallucinationFilter, TranscribeResult


def create_sine_wav(duration_s: float = 0.5, sample_rate: int = 16000) -> bytes:
    """Generates a simple 440 Hz sine wave as 16-bit mono WAV bytes."""
    t = np.linspace(0, duration_s, int(sample_rate * duration_s), endpoint=False)
    waveform = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(waveform.tobytes())

    return buffer.getvalue()


def test_hallucination_filter_patterns() -> None:
    assert HallucinationFilter.is_hallucination("")
    assert HallucinationFilter.is_hallucination("   ")
    assert HallucinationFilter.is_hallucination("Thanks for watching.")
    assert HallucinationFilter.is_hallucination("Thank you for watching!")
    assert HallucinationFilter.is_hallucination("Please subscribe")
    assert HallucinationFilter.is_hallucination("Subtitles by Amara.org")
    assert HallucinationFilter.is_hallucination("you")
    assert HallucinationFilter.is_hallucination("...")
    assert HallucinationFilter.is_hallucination("the the the the")
    assert HallucinationFilter.is_hallucination(
        "Patient reports mild headache", no_speech_prob=0.85
    )

    # Valid clinical text
    assert not HallucinationFilter.is_hallucination(
        "Patient has had mild fever for two days", no_speech_prob=0.1
    )
    assert not HallucinationFilter.is_hallucination(
        "Prescribed metformin 500 mg twice daily", no_speech_prob=0.05
    )


def test_pcm16_and_wav_conversion() -> None:
    wav_bytes = create_sine_wav(duration_s=0.25, sample_rate=16000)
    audio_np, sr = ASRService.wav_bytes_to_np(wav_bytes)

    assert sr == 16000
    assert len(audio_np) == int(16000 * 0.25)
    assert audio_np.dtype == np.float32

    raw_pcm = (np.ones(1600, dtype=np.int16) * 16384).tobytes()
    pcm_np = ASRService.pcm16_to_np(raw_pcm)
    assert len(pcm_np) == 1600
    assert np.allclose(pcm_np, 0.5, atol=0.01)


@pytest.mark.asyncio
async def test_asr_service_mock_transcribe(monkeypatch: pytest.MonkeyPatch) -> None:
    asr = ASRService(model_name="small.en")

    # Mock the synchronous model transcription to keep unit test fast and hermetic
    def mock_sync_transcribe(audio_array: np.ndarray, sample_rate: int = 16000) -> TranscribeResult:
        return TranscribeResult(
            text="Patient reports mild cough and headache",
            start_ms=0,
            end_ms=500,
            confidence=0.92,
            is_hallucination=False,
        )

    monkeypatch.setattr(asr, "_sync_transcribe", mock_sync_transcribe)

    dummy_audio = np.zeros(8000, dtype=np.float32)
    res = await asr.transcribe(dummy_audio)

    assert res.text == "Patient reports mild cough and headache"
    assert res.confidence == 0.92
    assert not res.is_hallucination

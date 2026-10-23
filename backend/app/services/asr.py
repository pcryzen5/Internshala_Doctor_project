"""Automated Speech Recognition (ASR) service powered by faster-whisper."""

import asyncio
import io
import logging
import re
import wave
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

# Known Whisper repetitive and hallucination phrases
HALLUCINATION_PATTERNS = [
    re.compile(r"^\s*thanks\s+for\s+watching\s*[.!]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*thank\s+you\s+for\s+watching\s*[.!]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*please\s+subscribe\s*[.!]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*subtitles\s+by\s+.*\s*$", re.IGNORECASE),
    re.compile(r"^\s*translated\s+by\s+.*\s*$", re.IGNORECASE),
    re.compile(r"^\s*you\s*$", re.IGNORECASE),
    re.compile(r"^\s*[.?!,;:\-_]+\s*$"),
]

MEDICAL_INITIAL_PROMPT = (
    "Medical consultation between clinician and patient discussing chief complaints, symptoms, "
    "medications, allergies, dosages, vital signs, physical examination, assessment, and "
    "treatment plan."
)


@dataclass
class TranscribeResult:
    text: str
    start_ms: int
    end_ms: int
    confidence: float
    is_hallucination: bool = False


class HallucinationFilter:
    """Detects and filters out empty, repetitive, or phantom Whisper output."""

    @staticmethod
    def is_hallucination(text: str, no_speech_prob: float = 0.0) -> bool:
        cleaned = text.strip()
        if not cleaned:
            return True

        # High probability that audio had no actual speech
        if no_speech_prob > 0.6:
            return True

        # Check regex blacklist
        for pattern in HALLUCINATION_PATTERNS:
            if pattern.search(cleaned):
                return True

        # Check for single word repeated excessively (e.g. "the the the the the")
        tokens = cleaned.lower().split()
        if len(tokens) >= 4 and len(set(tokens)) == 1:
            return True

        return False


class ASRService:
    """Thread-safe ASR service using faster-whisper with async queueing."""

    _instance: "ASRService | None" = None

    def __init__(self, model_name: str | None = None, device: str | None = None) -> None:
        self.model_name = model_name or settings.WHISPER_MODEL
        self.device = device or settings.WHISPER_DEVICE
        self.compute_type = settings.WHISPER_COMPUTE_TYPE
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="asr_worker")
        self._model: Any = None
        self._model_loaded = False
        self._lock = asyncio.Lock()
        self.active_tasks = 0
        self.max_queue_depth = 5

    @classmethod
    def get_instance(cls) -> "ASRService":
        if cls._instance is None:
            cls._instance = ASRService()
        return cls._instance

    def _load_model(self) -> Any:
        """Lazily load the faster-whisper model on first transcription request."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel

                logger.info(
                    "Loading faster-whisper model %s on device %s (%s)...",
                    self.model_name,
                    self.device,
                    self.compute_type,
                )
                self._model = WhisperModel(
                    self.model_name,
                    device=self.device,
                    compute_type=self.compute_type,
                )
                self._model_loaded = True
            except Exception as e:
                logger.error("Failed to load WhisperModel: %s. Falling back to stub.", str(e))
                self._model_loaded = False
        return self._model

    def _sync_transcribe(
        self,
        audio_array: np.ndarray,
        sample_rate: int = 16000,
    ) -> TranscribeResult:
        """Runs the synchronous faster-whisper transcription inside a thread."""
        model = self._load_model()
        if model is None:
            # Fallback if whisper weights cannot be loaded
            return TranscribeResult(
                text="[Audio transcribed]",
                start_ms=0,
                end_ms=int((len(audio_array) / sample_rate) * 1000),
                confidence=0.9,
                is_hallucination=False,
            )

        # Normalize float32 audio to [-1.0, 1.0]
        if audio_array.dtype == np.int16:
            audio_data = audio_array.astype(np.float32) / 32768.0
        else:
            audio_data = audio_array.astype(np.float32)

        segments, info = model.transcribe(
            audio_data,
            beam_size=5,
            vad_filter=False,  # Browser VAD already executed
            condition_on_previous_text=False,
            initial_prompt=MEDICAL_INITIAL_PROMPT,
        )

        texts: list[str] = []
        confidences: list[float] = []
        start_ms = 0
        end_ms = 0

        for seg in segments:
            texts.append(seg.text.strip())
            # Convert avg_logprob to pseudo-confidence
            conf = float(np.exp(seg.avg_logprob)) if seg.avg_logprob is not None else 0.85
            confidences.append(min(1.0, max(0.0, conf)))
            if start_ms == 0:
                start_ms = int(seg.start * 1000)
            end_ms = int(seg.end * 1000)

        full_text = " ".join(texts).strip()
        avg_confidence = float(np.mean(confidences)) if confidences else 0.85
        no_speech = float(info.no_speech_prob) if hasattr(info, "no_speech_prob") else 0.0

        is_hallucination = HallucinationFilter.is_hallucination(full_text, no_speech)

        return TranscribeResult(
            text="" if is_hallucination else full_text,
            start_ms=start_ms,
            end_ms=end_ms or int((len(audio_array) / sample_rate) * 1000),
            confidence=round(avg_confidence, 2),
            is_hallucination=is_hallucination,
        )

    async def transcribe(
        self,
        audio_array: np.ndarray,
        sample_rate: int = 16000,
    ) -> TranscribeResult:
        """Async entrypoint dispatching CPU work to threadpool."""
        if self.active_tasks >= self.max_queue_depth:
            raise RuntimeError("ASR service overloaded: maximum queue depth exceeded")

        self.active_tasks += 1
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(
                self.executor,
                self._sync_transcribe,
                audio_array,
                sample_rate,
            )
        finally:
            self.active_tasks -= 1

    @staticmethod
    def pcm16_to_np(pcm_bytes: bytes) -> np.ndarray:
        """Converts raw 16-bit signed PCM mono bytes to numpy float32 array."""
        int16_arr = np.frombuffer(pcm_bytes, dtype=np.int16)
        return int16_arr.astype(np.float32) / 32768.0

    @staticmethod
    def wav_bytes_to_np(wav_bytes: bytes) -> tuple[np.ndarray, int]:
        """Reads a WAV file buffer into a numpy float32 array and returns sample rate."""
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            frames = wf.readframes(n_frames)
            sampwidth = wf.getsampwidth()
            channels = wf.getnchannels()

            if sampwidth == 2:
                audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio = np.frombuffer(frames, dtype=np.float32)

            if channels > 1:
                # Average multi-channel to mono
                audio = audio.reshape(-1, channels).mean(axis=1)

            return audio, sample_rate

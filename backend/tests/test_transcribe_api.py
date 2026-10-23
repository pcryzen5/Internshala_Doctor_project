"""Integration tests for REST segment endpoints and WebSocket streaming."""

import json
import struct

import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient

from app.api.deps import get_asr_service
from app.main import app
from app.services.asr import ASRService, TranscribeResult
from tests.test_asr import create_sine_wav


class MockASRService(ASRService):
    """Hermetic mock for ASR in integration tests."""

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
def override_asr() -> None:
    app.dependency_overrides[get_asr_service] = lambda: MockASRService()
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rest_transcribe_segment_lifecycle() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create session first
        sess_res = await client.post("/api/v1/sessions", json={"language": "en"})
        session_id = sess_res.json()["id"]

        # 1. Upload audio segment WAV via REST
        wav_data = create_sine_wav(duration_s=0.5)
        files = {"audio": ("sample.wav", wav_data, "audio/wav")}
        data = {"seq": "1"}

        seg_res = await client.post(
            f"/api/v1/sessions/{session_id}/segments",
            files=files,
            data=data,
        )
        assert seg_res.status_code == 201, seg_res.text
        seg_data = seg_res.json()
        assert seg_data["seq"] == 1
        assert seg_data["text"] == "I have had fever since two days"
        assert seg_data["confidence"] == 0.94

        # 2. Get transcript
        trans_res = await client.get(f"/api/v1/sessions/{session_id}/transcript")
        assert trans_res.status_code == 200
        trans_data = trans_res.json()
        assert trans_data["text"] == "I have had fever since two days"
        assert len(trans_data["segments"]) == 1

        # 3. Patch segment edited text
        edit_res = await client.patch(
            f"/api/v1/sessions/{session_id}/segments/1",
            json={"edited_text": "I have had high fever since two days"},
        )
        assert edit_res.status_code == 200
        assert edit_res.json()["edited_text"] == "I have had high fever since two days"

        # 4. Verify updated combined transcript
        trans_res2 = await client.get(f"/api/v1/sessions/{session_id}/transcript")
        assert trans_res2.json()["text"] == "I have had high fever since two days"


def test_websocket_audio_streaming() -> None:
    client = TestClient(app)

    # Create session
    sess_res = client.post("/api/v1/sessions", json={"language": "en"})
    assert sess_res.status_code == 201
    session_id = sess_res.json()["id"]

    # Connect WebSocket
    with client.websocket_connect(f"/ws/sessions/{session_id}/audio") as ws:
        # Build binary frame: 4 bytes big endian header length + JSON header + raw PCM16 bytes
        header = json.dumps({"seq": 1, "sampleRate": 16000}).encode("utf-8")
        header_len_bytes = struct.pack(">I", len(header))
        pcm16_bytes = (np.ones(1600, dtype=np.int16) * 1000).tobytes()

        frame = header_len_bytes + header + pcm16_bytes
        ws.send_bytes(frame)

        # Receive transcript.segment event
        resp = ws.receive_json()
        assert resp["type"] == "transcript.segment"
        assert resp["seq"] == 1
        assert resp["text"] == "I have had fever since two days"
        assert resp["confidence"] == 0.94

        # Send session.stop
        ws.send_json({"type": "session.stop"})

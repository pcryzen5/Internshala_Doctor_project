"""Tests for LLM clinical analysis, schema validation, versioning, and export."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_analysis_empty_transcript_fails() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create session with no transcript segments
        sess_res = await client.post("/api/v1/sessions", json={"language": "en"})
        session_id = sess_res.json()["id"]

        # Attempt to analyze empty session
        res = await client.post(f"/api/v1/sessions/{session_id}/analyze", json={})
        assert res.status_code == 422
        assert "Cannot analyze an empty transcript" in res.json()["error"]["message"]


@pytest.mark.asyncio
async def test_golden_transcript_analysis_and_export() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create session
        sess_res = await client.post(
            "/api/v1/sessions",
            json={"language": "en", "patient_label": "Jane Doe"},
        )
        session_id = sess_res.json()["id"]

        # 2. Add transcript segments simulating a realistic consultation
        segments = [
            (1, "Clinician: Patient is Jane Doe, a 42 year old female."),
            (2, "Patient: Doctor, I have had fever since two days and severe headache."),
            (3, "Clinician: Do you have any vomiting or shortness of breath?"),
            (4, "Patient: No vomiting and no shortness of breath."),
            (5, "Clinician: Are you taking any medications?"),
            (6, "Patient: I am taking metformin 500 mg twice daily for my sugar."),
            (7, "Clinician: Any drug allergies?"),
            (8, "Patient: Yes, I am allergic to penicillin. It caused a rash."),
            (9, "Clinician: Your blood pressure is 120/80. Impression is acute viral syndrome."),
            (10, "Clinician: I will prescribe paracetamol 650 mg for the fever. Rest well."),
        ]

        # Use REST segment endpoint to add segments
        from tests.test_asr import create_sine_wav

        wav_bytes = create_sine_wav(0.1)
        for seq, text in segments:
            # Add segment via REST
            files = {"audio": ("sample.wav", wav_bytes, "audio/wav")}
            data = {"seq": str(seq)}
            add_res = await client.post(
                f"/api/v1/sessions/{session_id}/segments",
                files=files,
                data=data,
            )
            assert add_res.status_code == 201

            # Patch exact text
            await client.patch(
                f"/api/v1/sessions/{session_id}/segments/{seq}",
                json={"edited_text": text},
            )

        # 3. Analyze transcript with AI
        analyze_res = await client.post(
            f"/api/v1/sessions/{session_id}/analyze",
            json={"use_edited": True, "language": "en"},
        )
        assert analyze_res.status_code == 200, analyze_res.text
        data = analyze_res.json()

        assert data["version"] == 1
        summary = data["data"]

        # Assert extracted fields
        assert summary["patient"]["name"] == "Jane Doe"
        assert summary["patient"]["age"] == 42
        assert summary["patient"]["sex"] == "Female"

        assert summary["chief_complaint"]["text"] is not None
        assert summary["chief_complaint"]["evidence"] is not None

        # Assert positive vs negative symptoms strict separation
        pos_names = [s["name"] for s in summary["symptoms"]["positive"]]
        assert "Fever" in pos_names
        assert "Headache" in pos_names

        neg_names = [s["name"] for s in summary["symptoms"]["negative"]]
        assert "Vomiting" in neg_names
        assert "Shortness of breath" in neg_names
        # Negatives must not be in positives
        assert "Vomiting" not in pos_names

        # Assert medication and allergy
        med_names = [m["name"] for m in summary["medications"]]
        assert "Metformin" in med_names

        allergy_substances = [a["substance"] for a in summary["allergies"]]
        assert "Penicillin" in allergy_substances

        # Assert vital signs
        assert summary["observations"]["vitals"]["bp"] == "120/80 mmHg"

        # Assert absence of hallucinated fields
        assert len(summary["past_medical_history"]["surgeries"]) == 0
        assert len(summary["past_medical_history"]["hospitalisations"]) == 0

        # 4. Clinician Edit (PUT /summary -> version 2)
        summary["clinical_summary"] = "Clinician verified summary: Patient advised 3 days bed rest."
        edit_res = await client.put(
            f"/api/v1/sessions/{session_id}/summary",
            json=summary,
        )
        assert edit_res.status_code == 200
        edit_data = edit_res.json()
        assert edit_data["version"] == 2
        assert edit_data["source"] == "clinician_edit"

        # 5. List versions
        ver_res = await client.get(f"/api/v1/sessions/{session_id}/summaries")
        assert ver_res.status_code == 200
        versions = ver_res.json()
        assert len(versions) == 2

        # 6. Export plain text (Copy to Prescription)
        export_text_res = await client.get(f"/api/v1/sessions/{session_id}/export?format=text")
        assert export_text_res.status_code == 200
        text_content = export_text_res.text
        assert "Patient: Jane Doe, 42/Female" in text_content
        assert "Chief complaint:" in text_content
        assert "Symptoms: +" in text_content
        assert "; −" in text_content
        assert "Medications:" in text_content
        assert "Allergies:" in text_content

        # 7. Export JSON
        export_json_res = await client.get(f"/api/v1/sessions/{session_id}/export?format=json")
        assert export_json_res.status_code == 200
        json_content = export_json_res.json()
        assert json_content["patient"]["name"] == "Jane Doe"

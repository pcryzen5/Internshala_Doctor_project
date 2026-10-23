"""Integration tests for Sessions CRUD API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_session_lifecycle() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create session
        create_res = await client.post(
            "/api/v1/sessions",
            json={"language": "en", "patient_label": "John Doe"},
        )
        assert create_res.status_code == 201, create_res.text
        session_data = create_res.json()
        session_id = session_data["id"]
        assert session_data["status"] == "ready"
        assert session_data["language"] == "en"
        assert session_data["patient_label"] == "John Doe"

        # 2. Get session by ID
        get_res = await client.get(f"/api/v1/sessions/{session_id}")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == session_id

        # 3. List sessions
        list_res = await client.get("/api/v1/sessions")
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert list_data["total"] >= 1
        assert any(item["id"] == session_id for item in list_data["items"])

        # 4. Patch session
        patch_res = await client.patch(
            f"/api/v1/sessions/{session_id}",
            json={"patient_label": "Jane Doe", "status": "recording"},
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["patient_label"] == "Jane Doe"
        assert patch_res.json()["status"] == "recording"

        # 5. Clear session
        clear_res = await client.post(f"/api/v1/sessions/{session_id}/clear")
        assert clear_res.status_code == 200
        assert clear_res.json()["status"] == "ready"

        # 6. Delete session
        del_res = await client.delete(f"/api/v1/sessions/{session_id}")
        assert del_res.status_code == 204

        # 7. Verify soft delete (now 404)
        get_deleted_res = await client.get(f"/api/v1/sessions/{session_id}")
        assert get_deleted_res.status_code == 404

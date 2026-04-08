import pytest


@pytest.mark.asyncio
async def test_upload_media(client):
    files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
    resp = await client.post(
        "/api/medias", files=files, headers={"api-key": "test-key"}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["result"] is True
    assert "media_id" in data


@pytest.mark.asyncio
async def test_upload_media_unauthorized(client):
    files = {"file": ("test.jpg", b"data", "image/jpeg")}
    resp = await client.post(
        "/api/medias", files=files, headers={"api-key": "invalid-key"}
    )
    assert resp.status_code == 401
    assert resp.json()["result"] is False

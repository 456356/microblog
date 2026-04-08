import pytest


@pytest.mark.asyncio
async def test_get_my_profile(client):
    resp = await client.get("/api/users/me", headers={"api-key": "test-key"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] is True
    assert data["user"]["name"] == "Tester"
    assert isinstance(data["user"]["followers"], list)
    assert isinstance(data["user"]["following"], list)


@pytest.mark.asyncio
async def test_get_other_profile(client):
    resp = await client.get("/api/users/2", headers={"api-key": "test-key"})
    assert resp.status_code == 200
    assert resp.json()["user"]["name"] == "TesterTwo"


@pytest.mark.asyncio
async def test_get_non_existent_profile(client):
    resp = await client.get("/api/users/9999", headers={"api-key": "test-key"})
    assert resp.status_code == 404
    assert resp.json()["result"] is False

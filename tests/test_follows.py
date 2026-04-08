import pytest


@pytest.mark.asyncio
async def test_follow_and_unfollow(client):
    resp = await client.post("/api/users/2/follow", headers={"api-key": "test-key"})
    assert resp.status_code == 200
    assert resp.json()["result"] is True

    resp = await client.delete("/api/users/2/follow", headers={"api-key": "test-key"})
    assert resp.status_code == 200
    assert resp.json()["result"] is True


@pytest.mark.asyncio
async def test_follow_non_existent_user(client):
    resp = await client.post("/api/users/9999/follow", headers={"api-key": "test-key"})
    assert resp.status_code in [400, 404]
    assert resp.json()["result"] is False

import pytest


@pytest.mark.asyncio
async def test_like_and_unlike_tweet(client):
    create_resp = await client.post(
        "/api/tweets", json={"tweet_data": "Like test"}, headers={"api-key": "test-key"}
    )
    tweet_id = create_resp.json()["tweet_id"]

    resp = await client.post(
        f"/api/tweets/{tweet_id}/likes", headers={"api-key": "test-key-2"}
    )
    assert resp.status_code == 200
    assert resp.json()["result"] is True

    resp = await client.delete(
        f"/api/tweets/{tweet_id}/likes", headers={"api-key": "test-key-2"}
    )
    assert resp.status_code == 200
    assert resp.json()["result"] is True


@pytest.mark.asyncio
async def test_like_twice_fails(client):
    create_resp = await client.post(
        "/api/tweets",
        json={"tweet_data": "Double like"},
        headers={"api-key": "test-key"},
    )
    tweet_id = create_resp.json()["tweet_id"]

    await client.post(f"/api/tweets/{tweet_id}/likes", headers={"api-key": "test-key"})
    resp = await client.post(
        f"/api/tweets/{tweet_id}/likes", headers={"api-key": "test-key"}
    )
    assert resp.status_code in [400, 409]
    assert resp.json()["result"] is False

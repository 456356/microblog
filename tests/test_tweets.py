import pytest
from models.common import get_pool


@pytest.mark.asyncio
async def test_create_tweet(client):
    resp = await client.post(
        "/api/tweets",
        json={"tweet_data": "Hello", "tweet_media_ids": None},
        headers={"api-key": "test-key"},
    )
    assert resp.status_code == 201
    assert resp.json()["result"] is True
    assert "tweet_id" in resp.json()


@pytest.mark.asyncio
async def test_get_feed(client):
    resp = await client.get("/api/tweets", headers={"api-key": "test-key"})
    assert resp.status_code == 200
    assert resp.json()["result"] is True
    assert isinstance(resp.json()["tweets"], list)


@pytest.mark.asyncio
async def test_delete_tweet(client):
    # Создаём твит
    create_resp = await client.post(
        "/api/tweets",
        json={"tweet_data": "To be deleted"},
        headers={"api-key": "test-key"},
    )
    assert create_resp.status_code == 201
    tweet_id = create_resp.json()["tweet_id"]

    # Удаляем твит
    del_resp = await client.delete(
        f"/api/tweets/{tweet_id}", headers={"api-key": "test-key"}
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["result"] is True

    # Пытаемся удалить снова – должно быть 404 или 403
    del_resp2 = await client.delete(
        f"/api/tweets/{tweet_id}", headers={"api-key": "test-key"}
    )
    assert del_resp2.status_code in (403, 404)
    assert del_resp2.json()["result"] is False

    # Проверяем, что твит не появляется в ленте (если есть подписки)
    feed_resp = await client.get("/api/tweets", headers={"api-key": "test-key"})
    assert feed_resp.status_code == 200
    tweets = feed_resp.json()["tweets"]
    assert all(t["id"] != tweet_id for t in tweets)


@pytest.mark.asyncio
async def test_feed_order_by_popularity(client):
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (api_key, name) VALUES ('author1', 'Author One'), ('author2', 'Author Two')"
        )
        rows = await conn.fetch(
            "SELECT id, api_key FROM users WHERE api_key IN ('author1', 'author2')"
        )
        authors = {r["api_key"]: r["id"] for r in rows}
    author1_id = authors["author1"]
    author2_id = authors["author2"]

    # Подписываем test-key на авторов
    await client.post(
        f"/api/users/{author1_id}/follow", headers={"api-key": "test-key"}
    )
    await client.post(
        f"/api/users/{author2_id}/follow", headers={"api-key": "test-key"}
    )

    # Создаём твиты
    tweet1_resp = await client.post(
        "/api/tweets",
        json={"tweet_data": "Popular tweet"},
        headers={"api-key": "author1"},
    )
    tweet1_id = tweet1_resp.json()["tweet_id"]
    tweet2_resp = await client.post(
        "/api/tweets",
        json={"tweet_data": "Less popular"},
        headers={"api-key": "author2"},
    )
    tweet2_id = tweet2_resp.json()["tweet_id"]
    tweet3_resp = await client.post(
        "/api/tweets", json={"tweet_data": "Unpopular"}, headers={"api-key": "author1"}
    )
    tweet3_id = tweet3_resp.json()["tweet_id"]

    # Добавляем лайки: tweet1 – 2 лайка, tweet2 – 1 лайк
    await client.post(
        f"/api/tweets/{tweet1_id}/likes", headers={"api-key": "test-key-2"}
    )
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (api_key, name) VALUES ('liker', 'Liker')"
        )
    await client.post(f"/api/tweets/{tweet1_id}/likes", headers={"api-key": "liker"})
    await client.post(
        f"/api/tweets/{tweet2_id}/likes", headers={"api-key": "test-key-2"}
    )

    feed_resp = await client.get("/api/tweets", headers={"api-key": "test-key"})
    assert feed_resp.status_code == 200
    tweets = feed_resp.json()["tweets"]
    relevant = [t for t in tweets if t["id"] in (tweet1_id, tweet2_id, tweet3_id)]
    likes_counts = [len(t["likes"]) for t in relevant]
    assert likes_counts == sorted(likes_counts, reverse=True)

    # Очистка: сначала удаляем лайки, затем твиты, затем отписки, затем пользователей
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM likes WHERE tweet_id IN (SELECT id FROM tweets WHERE author_id IN ($1, $2))",
            author1_id,
            author2_id,
        )
        await conn.execute(
            "DELETE FROM tweets WHERE author_id IN ($1, $2)", author1_id, author2_id
        )
        await conn.execute(
            "DELETE FROM follows WHERE follower_id = 1 AND following_id IN ($1, $2)",
            author1_id,
            author2_id,
        )
        await conn.execute(
            "DELETE FROM users WHERE api_key IN ('author1', 'author2', 'liker')"
        )


@pytest.mark.asyncio
async def test_tweet_with_media(client, db_pool):
    # 1. Создаём отдельного пользователя для твита
    async with db_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (api_key, name) VALUES ('author-key', 'Author')"
        )
        author_row = await conn.fetchrow(
            "SELECT id FROM users WHERE api_key = 'author-key'"
        )
        author_id = author_row["id"]

    # 2. Подписываем test-key (id=1) на этого автора
    follow_resp = await client.post(
        f"/api/users/{author_id}/follow", headers={"api-key": "test-key"}
    )
    assert follow_resp.status_code == 200

    # 3. Загружаем картинку от имени автора
    files = {"file": ("test_image.jpg", b"fake image content", "image/jpeg")}
    media_resp = await client.post(
        "/api/medias", files=files, headers={"api-key": "author-key"}
    )
    assert media_resp.status_code == 201
    media_id = media_resp.json()["media_id"]

    # 4. Создаём твит с картинкой от автора
    tweet_payload = {
        "tweet_data": "Check out this picture!",
        "tweet_media_ids": [media_id],
    }
    tweet_resp = await client.post(
        "/api/tweets", json=tweet_payload, headers={"api-key": "author-key"}
    )
    assert tweet_resp.status_code == 201
    tweet_id = tweet_resp.json()["tweet_id"]

    # 5. Получаем ленту от test-key (подписан на автора)
    feed_resp = await client.get("/api/tweets", headers={"api-key": "test-key"})
    assert feed_resp.status_code == 200
    tweets = feed_resp.json()["tweets"]
    our_tweet = next((t for t in tweets if t["id"] == tweet_id), None)
    assert our_tweet is not None

    # 6. Проверяем attachments
    assert "attachments" in our_tweet
    assert len(our_tweet["attachments"]) == 1
    assert our_tweet["attachments"][0].startswith("media/")

    # 7. Проверяем, что файл существует на диске
    import os

    from models.common import settings

    file_path = settings.MEDIA_DIR / os.path.basename(our_tweet["attachments"][0])
    assert file_path.exists()

    # 8. Очистка: удаляем твит через API (каскадно удалит связи в tweet_media)
    await client.delete(f"/api/tweets/{tweet_id}", headers={"api-key": "author-key"})
    # Отписываемся
    await client.delete(
        f"/api/users/{author_id}/follow", headers={"api-key": "test-key"}
    )
    # Удаляем пользователя
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM users WHERE api_key = 'author-key'")

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app

TEST_DB_URL = "postgresql://postgres:postgres@localhost:5432/microblog_test"


@pytest.fixture(scope="session")
def event_loop():
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_pool():
    pool = await asyncpg.create_pool(TEST_DB_URL)
    async with pool.acquire() as conn:
        await conn.execute(
            "DROP TABLE IF EXISTS follows, likes, tweet_media, media, tweets, users CASCADE"
        )
        await conn.execute("""
            CREATE TABLE users(id SERIAL PRIMARY KEY, name VARCHAR, api_key VARCHAR UNIQUE);
            CREATE TABLE tweets(id SERIAL PRIMARY KEY, author_id INT REFERENCES users(id) ON DELETE CASCADE, content TEXT, created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE media(id SERIAL PRIMARY KEY, file_path VARCHAR UNIQUE);
            CREATE TABLE tweet_media(tweet_id INT REFERENCES tweets(id) ON DELETE CASCADE, media_id INT REFERENCES media(id) ON DELETE CASCADE, PRIMARY KEY(tweet_id, media_id));
            CREATE TABLE likes(user_id INT REFERENCES users(id) ON DELETE CASCADE, tweet_id INT REFERENCES tweets(id) ON DELETE CASCADE, PRIMARY KEY(user_id, tweet_id));
            CREATE TABLE follows(follower_id INT REFERENCES users(id) ON DELETE CASCADE, following_id INT REFERENCES users(id) ON DELETE CASCADE, PRIMARY KEY(follower_id, following_id), CHECK(follower_id!=following_id));
            INSERT INTO users(api_key, name) VALUES ('test-key', 'Tester'), ('test-key-2', 'TesterTwo');
        """)
    yield pool
    await pool.close()


@pytest_asyncio.fixture
async def client(db_pool):
    import models.common.db as db_module

    db_module._pool = db_pool
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as cli:
        yield cli

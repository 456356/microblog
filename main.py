"""Главный модуль FastAPI приложения.

Обеспечивает:
- Инициализацию базы данных и пула соединений.
- Настройку lifespan (создание таблиц, тестовых данных).
- Обработчики глобальных исключений.
- Подключение роутеров API.
- Раздачу статических файлов и SPA.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from controllers import follows, likes, media, tweets, users
from models.common import AppError, get_pool, init_db, settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управляет жизненным циклом приложения: запуск и завершение.

    При старте:
        - Инициализирует пул соединений с БД.
        - Создаёт таблицы, если их нет.
        - Заполняет тестовыми данными при пустой БД.
        - Создаёт директорию для медиафайлов.

    При завершении:
        - Закрывает пул соединений.
    """
    await init_db()
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name VARCHAR(100), api_key VARCHAR(64) UNIQUE);
            CREATE TABLE IF NOT EXISTS tweets (id SERIAL PRIMARY KEY, author_id INT REFERENCES users(id) ON DELETE CASCADE, content TEXT, created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS media (id SERIAL PRIMARY KEY, file_path VARCHAR(512) UNIQUE);
            CREATE TABLE IF NOT EXISTS tweet_media (tweet_id INT REFERENCES tweets(id) ON DELETE CASCADE, media_id INT REFERENCES media(id) ON DELETE CASCADE, PRIMARY KEY (tweet_id, media_id));
            CREATE TABLE IF NOT EXISTS likes (user_id INT REFERENCES users(id) ON DELETE CASCADE, tweet_id INT REFERENCES tweets(id) ON DELETE CASCADE, PRIMARY KEY (user_id, tweet_id));
            CREATE TABLE IF NOT EXISTS follows (follower_id INT REFERENCES users(id) ON DELETE CASCADE, following_id INT REFERENCES users(id) ON DELETE CASCADE, PRIMARY KEY (follower_id, following_id), CHECK (follower_id != following_id));
        """)
        exists = await conn.fetchval("SELECT 1 FROM users LIMIT 1")
        if not exists:
            await conn.execute("""
                INSERT INTO users (api_key, name) VALUES ('demo-key-1', 'Alice Dev'), ('demo-key-2', 'Bob Engineer'), ('test', 'John Test'), ('demo-key-3', 'Charlie Tester');
                INSERT INTO media (file_path) VALUES ('media/demo1.jpg'), ('media/demo2.png');
                INSERT INTO tweets (author_id, content) VALUES (1, 'Запускаю микроблог! 🚀'), (2, 'PostgreSQL + Docker = ❤️');
                INSERT INTO tweet_media (tweet_id, media_id) VALUES (1, 1);
                INSERT INTO likes (user_id, tweet_id) VALUES (2, 1), (1, 2);
                INSERT INTO follows (follower_id, following_id) VALUES (1, 2), (2, 1), (4, 1), (4, 2);
            """)
    os.makedirs(settings.MEDIA_DIR, exist_ok=True)
    yield
    await get_pool().close()


app = FastAPI(
    title="Microblog API", docs_url="/docs", redoc_url=None, lifespan=lifespan
)

# --- Обработчики исключений ---


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Преобразует бизнес-исключения (AppError) в единый формат ответа.

    Параметры:
        request: HTTP-запрос.
        exc: Исключение AppError.

    Возвращает:
        JSONResponse с полями result=False, error_type, error_message.
        HTTP-статус зависит от типа ошибки.
    """
    if exc.error_type == "AuthError":
        status_code = 401
    elif exc.error_type == "Forbidden":
        status_code = 403
    elif exc.error_type == "NotFound":
        status_code = 404
    elif exc.error_type == "Conflict":
        status_code = 409
    else:
        status_code = 400
    return JSONResponse(
        status_code=status_code,
        content={
            "result": False,
            "error_type": exc.error_type,
            "error_message": exc.message,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Обрабатывает ошибки валидации Pydantic.

    Параметры:
        request: HTTP-запрос.
        exc: Исключение валидации.

    Возвращает:
        JSONResponse с HTTP 422 и деталями ошибки.
    """
    return JSONResponse(
        status_code=422,
        content={
            "result": False,
            "error_type": "ValidationError",
            "error_message": str(exc),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Фолбэк для всех непредвиденных исключений.

    Параметры:
        request: HTTP-запрос.
        exc: Неперехваченное исключение.

    Возвращает:
        JSONResponse с HTTP 500 и общим сообщением об ошибке.
    """
    return JSONResponse(
        status_code=500,
        content={
            "result": False,
            "error_type": "ServerError",
            "error_message": "Internal server error",
        },
    )


# --- Подключение роутеров API ---
app.include_router(tweets.router)
app.include_router(media.router)
app.include_router(likes.router)
app.include_router(follows.router)
app.include_router(users.router)

# --- Раздача статики и SPA ---
if os.path.exists("/app/static"):
    app.mount("/static", StaticFiles(directory="/app/static"), name="static")
app.mount("/media", StaticFiles(directory=str(settings.MEDIA_DIR)), name="media")

"""Инициализация и управление пулом подключений к PostgreSQL."""

from typing import Optional

import asyncpg

from .config import settings

_pool: Optional[asyncpg.Pool] = None


async def init_db() -> asyncpg.Pool:
    """Создаёт и возвращает пул подключений к БД.

    Пул создаётся один раз и хранится в глобальной переменной _pool.

    Возвращает:
        Объект asyncpg.Pool.

    Исключения:
        Может бросить исключение при ошибке подключения.
    """
    global _pool
    if _pool is None:
        dsn = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        _pool = await asyncpg.create_pool(dsn=dsn)
    return _pool


def get_pool() -> asyncpg.Pool:
    """Возвращает активный пул подключений.

    Возвращает:
        asyncpg.Pool.

    Исключения:
        RuntimeError: если init_db() ещё не был вызван.
    """
    if _pool is None:
        raise RuntimeError("Database pool is not initialized. Call init_db() first.")
    return _pool

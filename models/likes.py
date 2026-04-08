"""Модуль лайков: поставить/убрать лайк с твита."""

from typing import Any, Dict

import asyncpg

from models.common import AppError, get_pool


async def repo_add_like(user_id: int, tweet_id: int) -> None:
    """Добавляет лайк в БД.

    Параметры:
        user_id: ID пользователя, ставящего лайк.
        tweet_id: ID твита.

    Исключения:
        AppError(Conflict) – лайк уже существует.
        AppError(NotFound) – пользователь или твит не найдены.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO likes (user_id, tweet_id) VALUES ($1, $2)",
                user_id,
                tweet_id,
            )
        except asyncpg.UniqueViolationError:
            raise AppError("Conflict", "Like already exists")
        except asyncpg.ForeignKeyViolationError as e:
            if "tweet_id" in str(e):
                raise AppError("NotFound", "Tweet not found")
            raise AppError("NotFound", "User not found")


async def repo_remove_like(user_id: int, tweet_id: int) -> bool:
    """Удаляет лайк из БД.

    Параметры:
        user_id: ID пользователя.
        tweet_id: ID твита.

    Возвращает:
        True, если лайк существовал и был удалён; иначе False.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        res = await conn.execute(
            "DELETE FROM likes WHERE user_id = $1 AND tweet_id = $2", user_id, tweet_id
        )
        return "DELETE 1" in res


async def svc_toggle_like(user: Dict, tweet_id: int, action: str) -> None:
    """Сервисная функция: поставить или убрать лайк.

    Параметры:
        user: данные текущего пользователя (с полем "id").
        tweet_id: ID твита.
        action: "add" – поставить лайк, "remove" – убрать.

    Исключения:
        AppError(NotFound) – при попытке убрать несуществующий лайк.
    """
    if action == "add":
        await repo_add_like(user["id"], tweet_id)
    else:
        if not await repo_remove_like(user["id"], tweet_id):
            raise AppError("NotFound", "Like not found")

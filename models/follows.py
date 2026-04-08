"""Модуль подписок: фолловинг/отписка (репозиторий + бизнес-логика)."""

from typing import Any, Dict

import asyncpg

from models.common import AppError, get_pool


async def repo_add_follow(follower_id: int, following_id: int) -> None:
    """Добавляет запись о подписке в БД.

    Параметры:
        follower_id: ID подписчика.
        following_id: ID пользователя, на которого подписываются.

    Исключения:
        AppError(Conflict) – если подписка уже существует.
        AppError(NotFound) – если follower_id или following_id не существуют.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO follows (follower_id, following_id) VALUES ($1, $2)",
                follower_id,
                following_id,
            )
        except asyncpg.UniqueViolationError:
            raise AppError("Conflict", "Already following this user")
        except asyncpg.ForeignKeyViolationError as e:
            if "following_id" in str(e):
                raise AppError("NotFound", "User to follow not found")
            raise AppError("NotFound", "Follower not found")


async def repo_remove_follow(follower_id: int, following_id: int) -> bool:
    """Удаляет запись о подписке из БД.

    Параметры:
        follower_id: ID подписчика.
        following_id: ID пользователя, от которого отписываются.

    Возвращает:
        True, если запись была удалена; False, если её не было.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        res = await conn.execute(
            "DELETE FROM follows WHERE follower_id = $1 AND following_id = $2",
            follower_id,
            following_id,
        )
        return "DELETE 1" in res


async def svc_toggle_follow(user: Dict, target_id: int, action: str) -> None:
    """Сервисная функция: подписаться или отписаться.

    Параметры:
        user: словарь с данными текущего пользователя (обязательно поле "id").
        target_id: ID целевого пользователя.
        action: "follow" или "unfollow".

    Исключения:
        AppError(NotFound) – при попытке отписаться от несуществующей подписки.
    """
    if action == "follow":
        await repo_add_follow(user["id"], target_id)
    else:
        if not await repo_remove_follow(user["id"], target_id):
            raise AppError("NotFound", "Follow relationship not found")

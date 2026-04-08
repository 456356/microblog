"""Модуль пользователей: получение профиля со списками подписчиков и подписок."""

from typing import Any, Dict, List

from pydantic import BaseModel

from models.common import AppError, get_pool


class UserProfile(BaseModel):
    """Схема профиля пользователя.

    Атрибуты:
        id: ID пользователя.
        name: имя.
        followers: список словарей {"id": int, "name": str} – подписчики.
        following: список словарей – те, на кого подписан пользователь.
    """

    id: int
    name: str
    followers: List[Dict[str, Any]]
    following: List[Dict[str, Any]]


async def repo_get_profile(user_id: int) -> Dict[str, Any]:
    """Загружает профиль пользователя из БД вместе с подписчиками и подписками.

    Параметры:
        user_id: ID пользователя.

    Возвращает:
        Словарь с ключами: id, name, followers, following.
        Если пользователь не найден – возвращает пустой словарь.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT id, name FROM users WHERE id = $1", user_id)
        if not user:
            return {}
        followers = await conn.fetch(
            "SELECT u.id, u.name FROM users u JOIN follows f ON u.id = f.follower_id WHERE f.following_id = $1",
            user_id,
        )
        following = await conn.fetch(
            "SELECT u.id, u.name FROM users u JOIN follows f ON u.id = f.following_id WHERE f.follower_id = $1",
            user_id,
        )
        return {
            "id": user["id"],
            "name": user["name"],
            "followers": [dict(r) for r in followers],
            "following": [dict(r) for r in following],
        }


async def svc_get_profile(user_id: int) -> UserProfile:
    """Сервис получения профиля.

    Параметры:
        user_id: ID пользователя.

    Возвращает:
        Объект UserProfile.

    Исключения:
        AppError(NotFound) – если пользователь не существует.
    """
    data = await repo_get_profile(user_id)
    if not data:
        raise AppError("NotFound", "User not found")
    return UserProfile(**data)

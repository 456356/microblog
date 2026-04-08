"""Модуль управления твитами: создание, удаление, получение ленты с сортировкой."""

import json
from typing import Any, Dict, List, Optional

import asyncpg
from pydantic import BaseModel, Field

from models.common import AppError, get_pool


class TweetCreate(BaseModel):
    """Схема для создания нового твита.

    Атрибуты:
        tweet_data: текст твита (1–280 символов).
        tweet_media_ids: опциональный список ID прикреплённых медиафайлов.
    """

    tweet_data: str = Field(..., min_length=1, max_length=280)
    tweet_media_ids: Optional[List[int]] = None


class Author(BaseModel):
    """Схема автора твита."""

    id: int
    name: str


class LikeInfo(BaseModel):
    """Схема информации о лайке."""

    user_id: int
    name: str


class TweetResponse(BaseModel):
    """Схема твита в ответе API (лента)."""

    id: int
    content: str
    attachments: List[str] = Field(default_factory=list)
    author: Author
    likes: List[LikeInfo] = Field(default_factory=list)


async def repo_create_tweet(author_id: int, content: str) -> int:
    """Создаёт запись твита в БД.

    Параметры:
        author_id: ID автора.
        content: текст твита.

    Возвращает:
        ID созданного твита.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "INSERT INTO tweets (author_id, content) VALUES ($1, $2) RETURNING id",
            author_id,
            content,
        )


async def repo_attach_media(tweet_id: int, media_ids: List[int]) -> None:
    """Прикрепляет список медиафайлов к твиту (связь многие-ко-многим).

    Параметры:
        tweet_id: ID твита.
        media_ids: список ID медиа.

    Исключения:
        AppError(NotFound) – если хотя бы один media_id не существует или твит не найден.
    """
    if not media_ids:
        return
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            await conn.executemany(
                "INSERT INTO tweet_media (tweet_id, media_id) VALUES ($1, $2)",
                [(tweet_id, mid) for mid in media_ids],
            )
        except asyncpg.ForeignKeyViolationError as e:
            if "media_id" in str(e):
                raise AppError("NotFound", "One or more media IDs do not exist")
            raise AppError("NotFound", "Tweet not found")


async def repo_delete_tweet(tweet_id: int, user_id: int) -> bool:
    """Удаляет твит, если его автор совпадает с user_id.

    Параметры:
        tweet_id: ID твита.
        user_id: ID текущего пользователя.

    Возвращает:
        True, если твит был удалён; False, если не найден или не принадлежит пользователю.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        res = await conn.execute(
            "DELETE FROM tweets WHERE id = $1 AND author_id = $2", tweet_id, user_id
        )
        return "DELETE 1" in res


async def repo_get_feed(user_id: int) -> List[Dict[str, Any]]:
    """Выбирает ленту твитов для пользователя.

    Логика:
        - Твиты авторов, на которых подписан user_id.
        - Включает автора, вложения (attachments) и список лайков.
        - Сортировка: по убыванию количества лайков, затем по дате создания (новые сверху).

    Параметры:
        user_id: ID пользователя, для которого строится лента.

    Возвращает:
        Список словарей с ключами: id, content, author, attachments, likes.
    """
    pool = get_pool()
    query = """
        SELECT 
            t.id, t.content,
            json_build_object('id', u.id, 'name', u.name) AS author,
            COALESCE(json_agg(m.file_path) FILTER (WHERE m.file_path IS NOT NULL), '[]'::json) AS attachments,
            COALESCE(json_agg(json_build_object('user_id', l.user_id, 'name', lu.name)) FILTER (WHERE l.user_id IS NOT NULL), '[]'::json) AS likes
        FROM tweets t
        JOIN users u ON t.author_id = u.id
        JOIN follows f ON t.author_id = f.following_id AND f.follower_id = $1
        LEFT JOIN tweet_media tm ON t.id = tm.tweet_id
        LEFT JOIN media m ON tm.media_id = m.id
        LEFT JOIN likes l ON t.id = l.tweet_id
        LEFT JOIN users lu ON l.user_id = lu.id
        GROUP BY t.id, u.id
        ORDER BY COUNT(l.user_id) DESC, t.created_at DESC
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, user_id)

        # Парсим JSON-строки в Python-объекты (для совместимости)
        result = []
        for row in rows:
            parsed = dict(row)
            if isinstance(parsed.get("author"), str):
                parsed["author"] = json.loads(parsed["author"])
            if isinstance(parsed.get("attachments"), str):
                parsed["attachments"] = json.loads(parsed["attachments"])
            if isinstance(parsed.get("likes"), str):
                parsed["likes"] = json.loads(parsed["likes"])
            result.append(parsed)
        return result


async def svc_create_tweet(user: Dict, data: TweetCreate) -> int:
    """Сервис создания твита.

    Параметры:
        user: данные текущего пользователя (поле "id").
        data: валидированные данные TweetCreate.

    Возвращает:
        ID созданного твита.
    """
    tid = await repo_create_tweet(user["id"], data.tweet_data)
    if data.tweet_media_ids:
        await repo_attach_media(tid, data.tweet_media_ids)
    return tid


async def svc_delete_tweet(user: Dict, tweet_id: int) -> None:
    """Сервис удаления твита.

    Параметры:
        user: текущий пользователь.
        tweet_id: ID удаляемого твита.

    Исключения:
        AppError(Forbidden) – если твит не найден или пользователь не автор.
    """
    if not await repo_delete_tweet(tweet_id, user["id"]):
        raise AppError("Forbidden", "Tweet not found or you are not the author")


async def svc_get_feed(user: Dict) -> List[TweetResponse]:
    """Сервис получения ленты.

    Параметры:
        user: текущий пользователь.

    Возвращает:
        Список объектов TweetResponse.
    """
    raw = await repo_get_feed(user["id"])
    return [TweetResponse(**r) for r in raw]

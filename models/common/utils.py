"""Вспомогательные утилиты: генерация уникальных имён файлов, валидация API-ключа."""

import os
import uuid
from typing import Any, Dict

from fastapi import Header

from .db import get_pool
from .exceptions import AppError


def generate_unique_filename(original_name: str) -> str:
    """Генерирует уникальное имя файла с сохранением расширения.

    Параметры:
        original_name: исходное имя файла (может быть без расширения).

    Возвращает:
        Строка вида <uuid4_hex>.<расширение> (если расширения нет, добавляется .jpg).
    """
    ext = os.path.splitext(original_name)[1] or ".jpg"
    return f"{uuid.uuid4().hex}{ext}"


async def validate_api_key(
    api_key: str = Header(..., alias="api-key")
) -> Dict[str, Any]:
    """Проверяет api-key в БД и возвращает данные пользователя.

    Параметры:
        api_key: значение заголовка api-key.

    Возвращает:
        Словарь с полями id и name пользователя.

    Исключения:
        AppError(AuthError): если ключ не найден.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, name FROM users WHERE api_key = $1", api_key
        )
    if not user:
        raise AppError("AuthError", "Invalid or missing api-key")
    return dict(user)

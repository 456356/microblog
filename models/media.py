"""Модуль управления медиафайлами: загрузка и сохранение на диск, запись в БД."""

import shutil

from fastapi import UploadFile

from models.common import generate_unique_filename, get_pool, settings


async def repo_create_media(file_path: str) -> int:
    """Сохраняет путь к файлу в таблице media и возвращает ID записи.

    Параметры:
        file_path: относительный путь к файлу (например, "media/abc.jpg").

    Возвращает:
        ID созданной записи media.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "INSERT INTO media (file_path) VALUES ($1) RETURNING id", file_path
        )


async def svc_upload_file(file: UploadFile) -> int:
    """Загружает файл на диск, генерирует уникальное имя и регистрирует в БД.

    Параметры:
        file: объект UploadFile от FastAPI.

    Возвращает:
        ID записи в таблице media.
    """
    unique_name = generate_unique_filename(file.filename or "upload")
    dest_path = settings.MEDIA_DIR / unique_name
    # Директория уже создана в lifespan, но на всякий случай:
    settings.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    media_id = await repo_create_media(f"media/{unique_name}")
    return media_id

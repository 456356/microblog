"""Глобальная конфигурация приложения (переменные окружения, пути)."""

import os
from pathlib import Path


class Settings:
    """Настройки приложения, загружаемые из переменных окружения.

    Атрибуты:
        DB_HOST: хост PostgreSQL (по умолчанию localhost, в Docker – db).
        DB_PORT: порт (5432).
        DB_USER: имя пользователя БД.
        DB_PASSWORD: пароль.
        DB_NAME: имя базы данных.
        MEDIA_DIR: директория для хранения загруженных медиафайлов.
    """

    DB_HOST: str = os.getenv("DB_HOST", "db")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    DB_NAME: str = os.getenv("DB_NAME", "microblog")
    MEDIA_DIR: Path = Path("/app/media")

settings = Settings()

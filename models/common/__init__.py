"""Пакет common: экспортирует общие компоненты для удобных импортов.

Содержит:
    settings: глобальную конфигурацию.
    init_db, get_pool: функции для работы с БД.
    AppError, app_exception_handler, validation_exception_handler: исключения и обработчики.
    generate_unique_filename, validate_api_key: утилиты.
"""

from .config import settings
from .db import get_pool, init_db
from .exceptions import AppError, app_exception_handler, validation_exception_handler
from .utils import generate_unique_filename, validate_api_key

__all__ = [
    "settings",
    "init_db",
    "get_pool",
    "AppError",
    "app_exception_handler",
    "validation_exception_handler",
    "generate_unique_filename",
    "validate_api_key",
]

"""Кастомные исключения и обработчики ошибок для FastAPI."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Базовое бизнес-исключение с типом и сообщением.

    Атрибуты:
        error_type: строковой идентификатор типа ошибки (например, "NotFound").
        message: человекочитаемое описание.
    """

    def __init__(self, error_type: str, message: str):
        self.error_type = error_type
        self.message = message
        super().__init__(message)


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для AppError (и других исключений) – унифицированный формат.

    Используется в main.py, но оставлен здесь для модульности.

    Параметры:
        request: HTTP-запрос.
        exc: исключение.

    Возвращает:
        JSONResponse с полями result, error_type, error_message.
    """
    if isinstance(exc, AppError):
        status_code = (
            400
            if "Conflict" in exc.error_type or "NotFound" in exc.error_type
            else (
                401
                if "Auth" in exc.error_type
                else 403 if "Forbidden" in exc.error_type else 500
            )
        )
        return JSONResponse(
            status_code=status_code,
            content={
                "result": False,
                "error_type": exc.error_type,
                "error_message": exc.message,
            },
        )
    return JSONResponse(
        status_code=500,
        content={
            "result": False,
            "error_type": "ServerError",
            "error_message": "Internal server error",
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Обработчик ошибок валидации Pydantic (422).

    Параметры:
        request: HTTP-запрос.
        exc: ошибка валидации.

    Возвращает:
        JSONResponse с HTTP 422.
    """
    return JSONResponse(
        status_code=422,
        content={
            "result": False,
            "error_type": "ValidationError",
            "error_message": str(exc),
        },
    )

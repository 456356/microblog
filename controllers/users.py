"""Контроллер эндпоинтов для профилей пользователей."""

from fastapi import APIRouter, Depends, Header
from models.common import validate_api_key
from models.users import svc_get_profile

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me")
async def get_my_profile(
    api_key: str = Header(..., alias="api-key"), user=Depends(validate_api_key)
) -> dict:
    """Получить профиль текущего авторизованного пользователя.

    Заголовки:
        api-key: API-ключ текущего пользователя.

    Возвращает:
        {"result": True, "user": UserProfile}.
    """
    return {"result": True, "user": await svc_get_profile(user["id"])}


@router.get("/{user_id}")
async def get_user_profile(
    user_id: int,
    api_key: str = Header(..., alias="api-key"),
    user=Depends(validate_api_key),
) -> dict:
    """Получить профиль любого пользователя по его ID.

    Параметры пути:
        user_id: ID пользователя.

    Заголовки:
        api-key: API-ключ текущего пользователя.

    Возвращает:
        {"result": True, "user": UserProfile}.
    """
    return {"result": True, "user": await svc_get_profile(user_id)}

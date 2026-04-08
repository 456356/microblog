"""Контроллер эндпоинтов для управления подписками (follow/unfollow)."""

from fastapi import APIRouter, Depends, Header
from models.common import validate_api_key
from models.follows import svc_toggle_follow

router = APIRouter(prefix="/api/users", tags=["Follows"])


@router.post("/{target_id}/follow")
async def follow_user(
    target_id: int,
    api_key: str = Header(..., alias="api-key"),
    user=Depends(validate_api_key),
) -> dict:
    """Подписаться на пользователя.

    Параметры пути:
        target_id: ID пользователя, на которого подписываются.

    Заголовки:
        api-key: API-ключ текущего пользователя.

    Возвращает:
        {"result": True} в случае успеха.
    """
    await svc_toggle_follow(user, target_id, "follow")
    return {"result": True}


@router.delete("/{target_id}/follow")
async def unfollow_user(
    target_id: int,
    api_key: str = Header(..., alias="api-key"),
    user=Depends(validate_api_key),
) -> dict:
    """Отписаться от пользователя.

    Параметры пути:
        target_id: ID пользователя, от которого отписываются.

    Заголовки:
        api-key: API-ключ текущего пользователя.

    Возвращает:
        {"result": True} в случае успеха.
    """
    await svc_toggle_follow(user, target_id, "unfollow")
    return {"result": True}

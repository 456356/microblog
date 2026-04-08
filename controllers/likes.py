"""Контроллер эндпоинтов для лайков твитов."""

from fastapi import APIRouter, Depends, Header
from models.common import validate_api_key
from models.likes import svc_toggle_like

router = APIRouter(prefix="/api/tweets", tags=["Likes"])


@router.post("/{tweet_id}/likes")
async def like_tweet(
    tweet_id: int,
    api_key: str = Header(..., alias="api-key"),
    user=Depends(validate_api_key),
) -> dict:
    """Поставить лайк на твит.

    Параметры пути:
        tweet_id: ID твита.

    Заголовки:
        api-key: API-ключ текущего пользователя.

    Возвращает:
        {"result": True} в случае успеха.
    """
    await svc_toggle_like(user, tweet_id, "add")
    return {"result": True}


@router.delete("/{tweet_id}/likes")
async def unlike_tweet(
    tweet_id: int,
    api_key: str = Header(..., alias="api-key"),
    user=Depends(validate_api_key),
) -> dict:
    """Убрать лайк с твита.

    Параметры пути:
        tweet_id: ID твита.

    Заголовки:
        api-key: API-ключ текущего пользователя.

    Возвращает:
        {"result": True} в случае успеха.
    """
    await svc_toggle_like(user, tweet_id, "remove")
    return {"result": True}

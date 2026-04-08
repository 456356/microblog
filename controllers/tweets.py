"""Контроллер эндпоинтов для работы с твитами (создание, удаление, лента)."""

from fastapi import APIRouter, Depends, Header
from models.common import validate_api_key
from models.tweets import TweetCreate, svc_create_tweet, svc_delete_tweet, svc_get_feed

router = APIRouter(prefix="/api/tweets", tags=["Tweets"])


@router.post("", status_code=201)
async def create_tweet(
    data: TweetCreate,
    api_key: str = Header(..., alias="api-key"),
    user=Depends(validate_api_key),
) -> dict:
    """Создать новый твит.

    Тело запроса (JSON):
        tweet_data: текст твита (1–280 символов).
        tweet_media_ids: опциональный список ID ранее загруженных медиа.

    Заголовки:
        api-key: API-ключ текущего пользователя.

    Возвращает:
        {"result": True, "tweet_id": id_созданного_твита}.
    """
    tid = await svc_create_tweet(user, data)
    return {"result": True, "tweet_id": tid}


@router.delete("/{tweet_id}")
async def delete_tweet(
    tweet_id: int,
    api_key: str = Header(..., alias="api-key"),
    user=Depends(validate_api_key),
) -> dict:
    """Удалить свой твит.

    Параметры пути:
        tweet_id: ID удаляемого твита.

    Заголовки:
        api-key: API-ключ текущего пользователя (должен быть автором).

    Возвращает:
        {"result": True} в случае успеха.
    """
    await svc_delete_tweet(user, tweet_id)
    return {"result": True}


@router.get("")
async def get_feed(
    api_key: str = Header(..., alias="api-key"), user=Depends(validate_api_key)
) -> dict:
    """Получить ленту твитов пользователя.

    Лента состоит из твитов тех, на кого подписан текущий пользователь.
    Сортировка: по убыванию количества лайков, затем по дате создания (новые сверху).

    Заголовки:
        api-key: API-ключ текущего пользователя.

    Возвращает:
        {"result": True, "tweets": [TweetResponse, ...]}.
    """
    tweets = await svc_get_feed(user)
    return {"result": True, "tweets": tweets}

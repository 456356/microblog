"""Контроллер эндпоинта для загрузки медиафайлов."""

from fastapi import APIRouter, Depends, File, Header, UploadFile
from models.common import validate_api_key
from models.media import svc_upload_file

router = APIRouter(prefix="/api/medias", tags=["Media"])


@router.post("", status_code=201)
async def upload_media(
    file: UploadFile = File(...),
    api_key: str = Header(..., alias="api-key"),
    user=Depends(validate_api_key),
) -> dict:
    """Загрузить медиафайл (изображение).

    Параметры формы:
        file: Загружаемый файл.

    Заголовки:
        api-key: API-ключ текущего пользователя.

    Возвращает:
        {"result": True, "media_id": id_загруженного_файла}.
    """
    media_id = await svc_upload_file(file)
    return {"result": True, "media_id": media_id}

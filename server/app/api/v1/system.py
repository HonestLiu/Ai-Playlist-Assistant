"""服务自身的健康检查。"""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.api.deps import SettingsDep
from app.schemas.common import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, summary="服务健康检查")
async def health(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=__version__,
        debug=settings.debug,
    )

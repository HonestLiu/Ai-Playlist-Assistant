"""Subsonic 相关的只读接口。Phase 2 会在这里继续扩充音乐库浏览。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.api.deps import SubsonicServiceDep, SubsonicSettingsServiceDep
from app.models.subsonic import ConnectionStatus
from app.subsonic.client import SubsonicClient

router = APIRouter(prefix="/subsonic", tags=["subsonic"])


@router.get("/status", response_model=ConnectionStatus, summary="当前连接状态")
async def connection_status(service: SubsonicServiceDep) -> ConnectionStatus:
    return await service.check()


def _sniff_media_type(data: bytes) -> str:
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if data.startswith(b"GIF8"):
        return "image/gif"
    if data.startswith(b"RIFF"):
        return "image/webp"
    return "image/jpeg"


@router.get("/cover/{cover_art_id}", summary="取回封面图（代理，前端不持有 Subsonic 凭据）")
async def cover_art(
    cover_art_id: str,
    settings_service: SubsonicSettingsServiceDep,
    size: int | None = Query(None, ge=16, le=800),
) -> Response:
    config = settings_service.resolve()
    if not config.is_complete:
        raise HTTPException(status_code=404, detail="Subsonic 未配置")
    async with SubsonicClient(config) as client:
        data = await client.get_cover_art(cover_art_id, size=size)
    return Response(content=data, media_type=_sniff_media_type(data))

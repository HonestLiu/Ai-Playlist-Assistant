"""播放历史接口：前端在歌曲真正开始播放时 POST 一次，用于驱动 Daily Mix 个性化。"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import PlayHistoryServiceDep, SessionDep

router = APIRouter(prefix="/play-history", tags=["play-history"])


class PlayHistoryIn(BaseModel):
    song_id: str


@router.post("", summary="记录一次播放（驱动 Daily Mix 个性化）")
def record_play(
    body: PlayHistoryIn,
    service: PlayHistoryServiceDep,
    session: SessionDep,
) -> dict:
    service.record(session, body.song_id)
    return {"ok": True}

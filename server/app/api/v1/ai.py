"""AI 推荐接口。"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Request

from app.ai.schemas import (
    DailyMixRequest,
    DailyMixResult,
    PlaylistRef,
    RecommendationResult,
)
from app.api.deps import (
    DailyMixServiceDep,
    PlaylistServiceDep,
    RecommendationServiceDep,
    SessionDep,
)
from app.core.logging import get_logger
from pydantic import BaseModel

logger = get_logger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


class RecommendRequest(BaseModel):
    query: str
    target_size: int | None = None
    create_playlist: bool = False
    playlist_name: str | None = None


def _default_playlist_name(query: str) -> str:
    head = query.strip().replace("\n", " ")[:20]
    stamp = datetime.now().strftime("%m%d %H:%M")
    return f"AI · {head} · {stamp}"


@router.post("/recommend", response_model=RecommendationResult, summary="自然语言生成歌单")
async def recommend(
    payload: RecommendRequest,
    rec_service: RecommendationServiceDep,
    playlist_service: PlaylistServiceDep,
    session: SessionDep,
) -> RecommendationResult:
    result = await rec_service.recommend(
        session, payload.query, target_size=payload.target_size
    )

    if payload.create_playlist and result.songs:
        name = payload.playlist_name or _default_playlist_name(payload.query)
        song_ids = [s.id for s in result.songs]
        record = await playlist_service.create(
            session,
            name=name,
            song_ids=song_ids,
            description=result.intent.summary,
            source="ai",
            query=payload.query,
        )
        result.playlist = PlaylistRef(
            id=str(record.id), subsonic_id=record.subsonic_id, name=record.name
        )
        logger.info("已为需求「%s」创建歌单 %s（%d 首）", payload.query, name, len(song_ids))

    return result


@router.post("/daily-mix", response_model=DailyMixResult, summary="生成/刷新今日每日推荐")
async def daily_mix(
    payload: DailyMixRequest,
    daily_mix_service: DailyMixServiceDep,
    session: SessionDep,
) -> DailyMixResult:
    return await daily_mix_service.generate(session, target_size=payload.target_size)


@router.get("/scheduler/status", summary="调度器状态")
async def scheduler_status(request: Request) -> dict:
    scheduler = request.app.state.scheduler
    return scheduler.status()


@router.post("/scheduler/trigger", summary="手动触发每日推荐（与 enabled 无关）")
async def scheduler_trigger(request: Request) -> dict:
    scheduler = request.app.state.scheduler
    ok = scheduler.trigger_now()
    return {"triggered": ok}

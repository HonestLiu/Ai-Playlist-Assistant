"""AI 推荐接口。"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.ai.schemas import (
    DailyMixRequest,
    DailyMixResult,
    PlaylistRef,
    RecommendationResult,
)
from app.api.deps import (
    ConfigStoreDep,
    DailyMixServiceDep,
    PlaylistServiceDep,
    RecommendationServiceDep,
    SessionDep,
)
from app.core.errors import AppError
from app.core.logging import get_logger
from app.database.config_store import ConfigStore
from pydantic import BaseModel

logger = get_logger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])

_TITLE_PREFIX = "AI · "
_DEFAULT_BASE_TITLE = "我的 AI 歌单"


class RecommendRequest(BaseModel):
    query: str
    target_size: int | None = None
    create_playlist: bool = False
    playlist_name: str | None = None


class CreatePlaylistRequest(BaseModel):
    query: str
    song_ids: list[str]
    name: str | None = None


def _apply_title_prefix(store: ConfigStore, base: str) -> str:
    """按用户偏好给歌单「基础标题」加或不加「AI · 」前缀。

    基础标题来自 AI 生成的 title（或用户改名），不含前缀；
    是否加前缀完全由用户偏好 ``playlist_title_prefix`` 决定（默认加）。
    """
    prefs = store.get_preferences() or {}
    use_prefix = prefs.get("playlist_title_prefix", True)
    base = (base or "").strip() or _DEFAULT_BASE_TITLE
    return f"{_TITLE_PREFIX}{base}" if use_prefix else base


@router.post("/recommend", response_model=RecommendationResult, summary="自然语言生成歌单")
async def recommend(
    payload: RecommendRequest,
    rec_service: RecommendationServiceDep,
    playlist_service: PlaylistServiceDep,
    store: ConfigStoreDep,
    session: SessionDep,
) -> RecommendationResult:
    result = await rec_service.recommend(
        session, payload.query, target_size=payload.target_size
    )

    if payload.create_playlist and result.songs:
        base = payload.playlist_name or result.title or payload.query
        name = _apply_title_prefix(store, base)
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


@router.post(
    "/recommend/playlist",
    response_model=PlaylistRef,
    summary="把已有推荐结果创建为 Subsonic 歌单（不重新生成）",
)
async def create_recommend_playlist(
    payload: CreatePlaylistRequest,
    playlist_service: PlaylistServiceDep,
    store: ConfigStoreDep,
    session: SessionDep,
) -> PlaylistRef:
    """直接按当前推荐结果的 song_ids 在 Subsonic 创建歌单。

    与 ``/recommend?create_playlist=true`` 不同，这里**不会重新跑 LLM 推荐**，
    只是把用户已经看到的歌单落盘到 Subsonic，因此更快、且歌单内容一致。
    歌单标题使用 AI 生成的 title（或前端传入的改名），并按用户偏好决定是否带「AI · 」前缀。
    """
    if not payload.song_ids:
        raise AppError(
            "song_ids 为空，无法创建歌单",
            code="invalid_argument",
            status_code=400,
        )
    base = payload.name or payload.query
    name = _apply_title_prefix(store, base)
    record = await playlist_service.create(
        session,
        name=name,
        song_ids=list(payload.song_ids),
        description=payload.query,
        source="ai",
        query=payload.query,
    )
    logger.info("已按需求「%s」创建 Subsonic 歌单 %s（%d 首）", payload.query, name, len(payload.song_ids))
    return PlaylistRef(id=str(record.id), subsonic_id=record.subsonic_id, name=record.name)


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

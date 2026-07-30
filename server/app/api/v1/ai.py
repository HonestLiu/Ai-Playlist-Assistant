"""AI 推荐接口。"""

from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter

from app.ai.schemas import (
    DailyMixRequest,
    DailyMixResult,
    PlaylistRef,
    RecommendationResult,
)
from app.api.deps import PlaylistServiceDep, RecommendationServiceDep, SessionDep
from app.core.logging import get_logger
from pydantic import BaseModel

logger = get_logger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


class RecommendRequest(BaseModel):
    query: str
    target_size: int | None = None
    create_playlist: bool = False
    playlist_name: str | None = None


# 按星期轮转的每日主题；描述里嵌入 mock provider 能识别的语言/流派关键词，
# 这样在 mock 模式下「每日推荐」每天也有差异；接真实 LLM 后差异更自然。
_DAILY_THEMES = [
    ("元气开场 · 日语流行", "轻快明亮的日语流行，开启新的一周"),
    ("动漫时间 · 动漫歌曲", "动漫歌曲合集，唤起中二魂"),
    ("燃向中点 · 摇滚", "高能量的摇滚，撑过一周中点"),
    ("专注流 · 纯音乐", "适合写代码和专注工作的纯音乐与后摇"),
    ("英文夜晚 · 放松", "放松的英文歌，迎接周末"),
    ("悠闲周末 · 流行", "慵懒的流行歌，慢节奏过周末"),
    ("怀旧回顾 · 经典", "安静的经典老歌，回顾这一周"),
]


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
    rec_service: RecommendationServiceDep,
    playlist_service: PlaylistServiceDep,
    session: SessionDep,
) -> DailyMixResult:
    today = date.today()
    date_str = today.isoformat()
    name = f"每日推荐 {date_str}"
    title, desc = _DAILY_THEMES[today.weekday()]
    query = f"每日推荐（{title}）：{desc}"

    result = await rec_service.recommend(
        session, query, target_size=payload.target_size
    )
    song_ids = [s.id for s in result.songs]

    existing = playlist_service.get_by_name(session, name)
    refreshed = False
    record = None
    if song_ids:
        if existing:
            record = await playlist_service.update(
                session,
                existing.id,
                song_ids=song_ids,
                query=query,
                description=result.intent.summary,
            )
            refreshed = True
        else:
            record = await playlist_service.create(
                session,
                name=name,
                song_ids=song_ids,
                description=result.intent.summary,
                source="daily_mix",
                query=query,
            )

    playlist = (
        PlaylistRef(id=str(record.id), subsonic_id=record.subsonic_id, name=record.name)
        if record
        else None
    )
    logger.info(
        "每日推荐 %s：%s（%d 首，主题=%s）",
        date_str,
        "刷新" if refreshed else ("新建" if record else "无歌曲"),
        len(song_ids),
        title,
    )
    return DailyMixResult(
        query=query,
        theme=title,
        recommendation=result,
        playlist=playlist,
        refreshed=refreshed,
        created=bool(record and not refreshed),
    )

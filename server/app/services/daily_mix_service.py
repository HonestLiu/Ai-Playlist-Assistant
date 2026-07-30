"""每日推荐编排服务。

把「每日推荐」的生成逻辑从 API 层抽出来，让定时调度器也能直接复用，
不必走 HTTP。逻辑与 ``POST /ai/daily-mix`` 端点一致：按星期轮转主题、
同日再生成则刷新而非新建。
"""

from __future__ import annotations

from datetime import date

from sqlmodel import Session

from app.ai.schemas import DailyMixResult, PlaylistRef
from app.core.logging import get_logger
from app.services.playlist_service import PlaylistService
from app.services.recommendation_service import RecommendationService

logger = get_logger(__name__)

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


class DailyMixService:
    def __init__(
        self,
        recommendation_service: RecommendationService,
        playlist_service: PlaylistService,
    ) -> None:
        self._rec = recommendation_service
        self._playlist = playlist_service

    async def generate(
        self, session: Session, *, target_size: int | None = None
    ) -> DailyMixResult:
        today = date.today()
        date_str = today.isoformat()
        name = f"每日推荐 {date_str}"
        title, desc = _DAILY_THEMES[today.weekday()]
        query = f"每日推荐（{title}）：{desc}"

        result = await self._rec.recommend(session, query, target_size=target_size)
        song_ids = [s.id for s in result.songs]

        existing = self._playlist.get_by_name(session, name)
        refreshed = False
        record = None
        if song_ids:
            if existing:
                record = await self._playlist.update(
                    session,
                    existing.id,
                    song_ids=song_ids,
                    query=query,
                    description=result.intent.summary,
                )
                refreshed = True
            else:
                record = await self._playlist.create(
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

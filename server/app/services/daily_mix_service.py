"""每日推荐编排服务。

把「每日推荐」的生成逻辑从 API 层抽出来，让定时调度器也能直接复用，
不必走 HTTP。逻辑与 ``POST /ai/daily-mix`` 端点一致：同日再生成则刷新而非新建。

个性化：根据**播放历史**与**已有歌单**聚合出用户口味画像（Top 艺术家 / Top 流派 /
最近播放），据此偏置推荐；完全没有历史时回退到周几轮转主题，保证首跑也有差异。
"""

from __future__ import annotations

from collections import Counter
from datetime import date

from sqlmodel import Session, select

from app.ai.schemas import DailyMixResult, PlaylistRef
from app.core.logging import get_logger
from app.database.models import Playlist, Song
from app.services.play_history_service import PlayHistoryService
from app.services.playlist_service import PlaylistService
from app.services.recommendation_service import RecommendationService

logger = get_logger(__name__)

# 无任何历史时的回退主题；描述里嵌入 mock provider 能识别的语言/流派关键词，
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

        profile = self._build_profile(session)
        query = self._build_query(profile, today)
        personalized = bool(profile["top_artists"] or profile["top_genres"])

        result = await self._rec.recommend(
            session,
            query,
            target_size=target_size,
            preferred_artists=profile["top_artists"],
            preferred_genres=profile["top_genres"],
            exclude_song_ids=profile["recent_song_ids"],
        )
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
        theme = "今日为你" if personalized else _DAILY_THEMES[today.weekday()][0]
        logger.info(
            "每日推荐 %s：%s（%d 首，个性化=%s，偏好艺术家=%s）",
            date_str,
            "刷新" if refreshed else ("新建" if record else "无歌曲"),
            len(song_ids),
            personalized,
            profile["top_artists"][:3],
        )
        return DailyMixResult(
            query=query,
            theme=theme,
            recommendation=result,
            playlist=playlist,
            refreshed=refreshed,
            created=bool(record and not refreshed),
        )

    # ------------------------------------------------------------------ 偏好画像
    def _build_profile(self, session: Session) -> dict:
        ph = PlayHistoryService()
        top_artists = ph.top_artists(session, 8)
        top_genres = ph.top_genres(session, 6)
        recent = ph.recent_song_ids(session, 40)
        # 没播过任何歌时，用「已有歌单」的分布当作初始口味
        if not top_artists and not top_genres:
            top_artists, top_genres = self._profile_from_playlists(session)
        return {
            "top_artists": top_artists,
            "top_genres": top_genres,
            "recent_song_ids": recent,
        }

    def _profile_from_playlists(self, session: Session) -> tuple[list[str], list[str]]:
        records = session.exec(select(Playlist)).all()
        ids: list[str] = []
        for r in records:
            ids.extend(r.song_ids or [])
        if not ids:
            return [], []
        rows = session.exec(select(Song).where(Song.id.in_(ids))).all()
        artist_c = Counter(s.artist_name for s in rows if s.artist_name)
        genre_c = Counter(s.genre for s in rows if s.genre)
        return (
            [a for a, _ in artist_c.most_common(8)],
            [g for g, _ in genre_c.most_common(6)],
        )

    def _build_query(self, profile: dict, today: date) -> str:
        if profile["top_artists"] or profile["top_genres"]:
            bits = ["今日每日推荐：结合我的收听偏好生成一份歌单。"]
            if profile["top_artists"]:
                bits.append(f"我常听的艺术家：{'、'.join(profile['top_artists'][:5])}。")
            if profile["top_genres"]:
                bits.append(f"偏好的流派：{'、'.join(profile['top_genres'][:4])}。")
            bits.append("在熟悉口味与新鲜探索之间取得平衡，避免与最近听过的歌重复。")
            return "".join(bits)
        title, desc = _DAILY_THEMES[today.weekday()]
        return f"每日推荐（{title}）：{desc}"

"""推荐编排服务（AI Agent 的核心管线）。

流程：自然语言 → ① 意图解析（LLM）→ ② 本地库候选召回 → ③ 候选选择（LLM）
→ ④ 组装结果。建歌单是可选的第 ⑤ 步，由 API 层在拿到结果后再决定，
本服务只负责「出歌单」，不碰 Subsonic 写操作，职责更清晰。
"""

from __future__ import annotations

from typing import Optional

from sqlmodel import Session, func, or_, select

from app.ai.prompts.intent import build_intent_messages
from app.ai.prompts.selection import build_selection_messages
from app.ai.providers import ChatRequest, get_provider
from app.ai.providers.base import LLMProvider
from app.ai.schemas import (
    PlaylistIntent,
    RecommendationResult,
    RecommendedSong,
    SongSelection,
)
from app.core.config import LLMSettings
from app.core.logging import get_logger
from app.database.models import Song
from app.services.llm_settings_service import LLMSettingsService
from app.services.settings_service import SubsonicSettingsService

logger = get_logger(__name__)

_CANDIDATE_CAP = 250
_MIN_RECALL = 40


class RecommendationService:
    def __init__(
        self,
        llm_settings_service: LLMSettingsService,
        subsonic_settings_service: SubsonicSettingsService,
    ) -> None:
        self._llm = llm_settings_service
        self._subsonic = subsonic_settings_service

    # ------------------------------------------------------------------ 主入口
    async def recommend(
        self,
        session: Session,
        query: str,
        *,
        target_size: int | None = None,
        provider: LLMProvider | None = None,
    ) -> RecommendationResult:
        settings = self._llm.resolve()
        provider = provider or get_provider(settings)

        # ① 意图解析
        intent = await self._parse_intent(provider, settings, query)
        if target_size:
            intent.target_size = target_size

        # ② 候选召回
        candidates = self._retrieve_candidates(session, intent)
        if not candidates:
            return RecommendationResult(
                query=query,
                intent=intent,
                provider=settings.provider,
                total_candidates=0,
                songs=[],
            )

        # ③ 候选选择
        chosen = await self._select(provider, settings, intent, candidates)

        # ④ 组装
        by_id = {s.id: s for s in candidates}
        songs: list[RecommendedSong] = []
        for sel in chosen:
            row = by_id.get(sel.song_id)
            if row is None:
                continue
            songs.append(
                RecommendedSong(
                    id=row.id,
                    title=row.title,
                    artist_name=row.artist_name,
                    album_name=row.album_name,
                    year=row.year,
                    duration=row.duration,
                    reason=sel.reason or None,
                )
            )
        total_duration = sum((s.duration or 0) for s in songs)
        return RecommendationResult(
            query=query,
            intent=intent,
            provider=settings.provider,
            total_candidates=len(candidates),
            songs=songs,
            total_duration=total_duration,
        )

    # ------------------------------------------------------------------ ① 意图解析
    async def _parse_intent(
        self, provider: LLMProvider, settings: LLMSettings, query: str
    ) -> PlaylistIntent:
        genres, year_min, year_max = self._library_profile()
        messages = build_intent_messages(
            query, genres=genres, year_min=year_min, year_max=year_max
        )
        request = ChatRequest(
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        try:
            data = await provider.chat_json(request)
            return PlaylistIntent.model_validate(data)
        except Exception as exc:  # 解析失败降级为最小意图
            logger.warning("意图解析失败，降级为最小意图: %s", exc)
            return PlaylistIntent(summary=query, target_size=20)

    # ------------------------------------------------------------------ ② 候选召回
    def _retrieve_candidates(self, session: Session, intent: PlaylistIntent) -> list[Song]:
        conditions = self._build_conditions(intent)
        stmt = select(Song)
        if conditions:
            stmt = stmt.where(or_(*conditions))
        stmt = stmt.limit(_CANDIDATE_CAP)
        rows = list(session.exec(stmt).all())

        # 召回太少时，去掉 genre 条件再宽一次（保底）
        if len(rows) < _MIN_RECALL and conditions:
            genre_conditions = self._build_conditions(intent, genre_only=True)
            others = [c for c in conditions if c not in genre_conditions]
            if others:
                stmt2 = select(Song).where(or_(*others)).limit(_CANDIDATE_CAP)
                rows = list(session.exec(stmt2).all())
        return rows

    def _build_conditions(self, intent: PlaylistIntent, *, genre_only: bool = False):
        conds = []
        if not genre_only:
            if intent.min_year:
                conds.append(Song.year >= intent.min_year)
            if intent.max_year:
                conds.append(Song.year <= intent.max_year)
            if intent.decade:
                conds.append(Song.year >= intent.decade)
                conds.append(Song.year < intent.decade + 10)
            for kw in intent.keywords or []:
                like = f"%{kw}%"
                conds.append(Song.title.ilike(like))
                conds.append(Song.artist_name.ilike(like))
            for kw in intent.exclude_keywords or []:
                like = f"%{kw}%"
                conds.append(Song.title.not_ilike(like))
                conds.append(Song.artist_name.not_ilike(like))
        for g in intent.genres or []:
            conds.append(Song.genre.ilike(f"%{g}%"))
        return conds

    # ------------------------------------------------------------------ ③ 候选选择
    async def _select(
        self,
        provider: LLMProvider,
        settings: LLMSettings,
        intent: PlaylistIntent,
        candidates: list[Song],
    ) -> list:
        cand_dicts = [
            {
                "id": s.id,
                "title": s.title,
                "artist": s.artist_name,
                "album": s.album_name,
                "year": s.year,
                "genre": s.genre,
            }
            for s in candidates
        ]
        messages = build_selection_messages(intent.summary, cand_dicts, intent.target_size)
        request = ChatRequest(
            messages=messages,
            temperature=settings.temperature,
            response_format={"type": "json_object"},
        )
        try:
            data = await provider.chat_json(request)
            selection = SongSelection.model_validate(data)
        except Exception as exc:
            logger.warning("候选选择失败，降级为顺序截取: %s", exc)
            selection = SongSelection(
                songs=[{"song_id": s.id, "reason": ""} for s in candidates[: intent.target_size]]
            )
        valid = {s.id for s in candidates}
        chosen = [c for c in selection.songs if c.song_id in valid][: intent.target_size]
        return chosen

    # ------------------------------------------------------------------ 曲库画像
    def _library_profile(self) -> tuple[list[str], Optional[int], Optional[int]]:
        from app.database.engine import _engine as engine

        with Session(engine) as s:
            genres = s.exec(select(Song.genre).where(Song.genre.is_not(None)).distinct()).all()
            year_min = s.exec(select(func.min(Song.year))).first()
            year_max = s.exec(select(func.max(Song.year))).first()
        gset = []
        for g in genres:
            if g and g not in gset:
                gset.append(g)
        return gset[:30], year_min, year_max

"""歌单服务：在 Subsonic 创建/删除歌单，并同步本地记录供页面展示。"""

from __future__ import annotations

from sqlmodel import Session, func, select

from app.core.logging import get_logger
from app.database.models import Playlist, Song
from app.services.settings_service import SubsonicSettingsService
from app.subsonic.client import SubsonicClient

logger = get_logger(__name__)


class PlaylistService:
    def __init__(self, subsonic_settings_service: SubsonicSettingsService) -> None:
        self._sub = subsonic_settings_service

    # ------------------------------------------------------------------ 创建
    async def create(
        self,
        session: Session,
        *,
        name: str,
        song_ids: list[str],
        description: str | None = None,
        source: str = "ai",
        query: str | None = None,
    ) -> Playlist:
        config = self._sub.resolve()
        async with SubsonicClient(config) as client:
            subsonic_id = await client.create_playlist(name, song_ids)

        duration = (
            session.exec(
                select(func.coalesce(func.sum(Song.duration), 0)).where(
                    Song.id.in_(song_ids)
                )
            ).first()
            or 0
        )
        record = Playlist(
            subsonic_id=subsonic_id,
            name=name,
            description=description,
            source=source,
            query=query,
            song_ids=list(song_ids),
            song_count=len(song_ids),
            duration=int(duration or 0),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        logger.info("已创建歌单 %s（subsonic_id=%s, %d 首）", name, subsonic_id, len(song_ids))
        return record

    # ------------------------------------------------------------------ 查询
    def list(self, session: Session, *, source: str | None = None) -> list[Playlist]:
        stmt = select(Playlist)
        if source:
            stmt = stmt.where(Playlist.source == source)
        stmt = stmt.order_by(Playlist.created_at.desc())
        return list(session.exec(stmt).all())

    def get(self, session: Session, playlist_id: int) -> Playlist | None:
        return session.get(Playlist, playlist_id)

    def get_by_name(self, session: Session, name: str) -> Playlist | None:
        return session.exec(
            select(Playlist).where(Playlist.name == name)
        ).first()

    # ------------------------------------------------------------------ 更新
    async def update(
        self,
        session: Session,
        playlist_id: int,
        *,
        name: str | None = None,
        song_ids: list[str] | None = None,
        description: str | None = None,
        query: str | None = None,
    ) -> Playlist | None:
        record = session.get(Playlist, playlist_id)
        if record is None:
            return None

        new_name = name if name is not None else record.name
        new_song_ids = list(song_ids) if song_ids is not None else record.song_ids

        duration = record.duration
        if song_ids is not None:
            duration = (
                session.exec(
                    select(func.coalesce(func.sum(Song.duration), 0)).where(
                        Song.id.in_(new_song_ids)
                    )
                ).first()
                or 0
            )

        config = self._sub.resolve()
        async with SubsonicClient(config) as client:
            await client.update_playlist(
                record.subsonic_id, name=new_name, song_ids=list(new_song_ids)
            )

        record.name = new_name
        record.song_ids = list(new_song_ids)
        record.song_count = len(new_song_ids)
        record.duration = int(duration or 0)
        if description is not None:
            record.description = description
        if query is not None:
            record.query = query
        session.add(record)
        session.commit()
        session.refresh(record)
        logger.info(
            "已更新歌单 %s（subsonic_id=%s, %d 首）",
            new_name,
            record.subsonic_id,
            len(new_song_ids),
        )
        return record

    # ------------------------------------------------------------------ 删除
    async def delete(self, session: Session, playlist_id: int) -> bool:
        record = session.get(Playlist, playlist_id)
        if record is None:
            return False
        config = self._sub.resolve()
        try:
            async with SubsonicClient(config) as client:
                await client.delete_playlist(record.subsonic_id)
        except Exception as exc:  # Subsonic 侧删不掉也保留本地清理，但记日志
            logger.warning("删除 Subsonic 歌单失败（本地仍清理）: %s", exc)
        session.delete(record)
        session.commit()
        return True

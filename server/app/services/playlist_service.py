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

    # ------------------------------------------------------------------ 服务器同步
    async def sync_from_subsonic(self, session: Session) -> dict[str, int]:
        """把 Subsonic 服务器上已有的歌单拉进本地库。

        - 本地没有的（按 ``subsonic_id`` 匹配）→ 新建，``source="server"``；
        - 已有但名称/歌曲数/时长有变化 → 拉详情更新（含歌曲列表）；
        - ``source="server"`` 且服务器上已删除 → 本地同步删除
          （AI/每日推荐歌单不动，避免误删本地元信息）。
        """

        config = self._sub.resolve()
        imported = updated = removed = 0

        async with SubsonicClient(config) as client:
            remote = await client.get_playlists()
            remote_ids = {p.id for p in remote}
            local = {
                r.subsonic_id: r for r in session.exec(select(Playlist)).all()
            }

            for summary in remote:
                record = local.get(summary.id)
                if record is None:
                    detail = await client.get_playlist(summary.id)
                    record = Playlist(
                        subsonic_id=detail.id,
                        name=detail.name,
                        description=detail.comment,
                        source="server",
                        song_ids=list(detail.song_ids),
                        song_count=detail.song_count or len(detail.song_ids),
                        duration=detail.duration or 0,
                    )
                    if detail.created:
                        record.created_at = detail.created
                    session.add(record)
                    imported += 1
                elif (
                    record.name != summary.name
                    or record.song_count != summary.song_count
                    # 该服务器摘要/详情接口的时长存在 ±1s 舍入误差，容忍 2s
                    or abs(record.duration - summary.duration) > 2
                ):
                    detail = await client.get_playlist(summary.id)
                    record.name = detail.name
                    record.song_ids = list(detail.song_ids)
                    record.song_count = detail.song_count or len(detail.song_ids)
                    record.duration = detail.duration or 0
                    if detail.comment is not None:
                        record.description = detail.comment
                    session.add(record)
                    updated += 1

        for sid, record in local.items():
            if sid not in remote_ids and record.source == "server":
                session.delete(record)
                removed += 1

        session.commit()
        total = len(session.exec(select(Playlist)).all())
        logger.info(
            "歌单同步完成：新增 %d、更新 %d、移除 %d，本地共 %d 份",
            imported,
            updated,
            removed,
            total,
        )
        return {
            "imported": imported,
            "updated": updated,
            "removed": removed,
            "total": total,
        }

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

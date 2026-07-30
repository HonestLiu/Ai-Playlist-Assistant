"""浏览服务。

只从本地 SQLite 读，不碰 Subsonic。所有查询都返回 ``(items, total)`` 以便 API
组装分页响应。过滤条件用参数化 ``like`` / 等值，安全且可空。
"""

from __future__ import annotations

from sqlmodel import Session, func, select

from app.database import models


class BrowseService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _paginate(self, base_stmt, *, limit: int, offset: int):
        total = self._session.exec(
            select(func.count()).select_from(base_stmt.subquery())
        ).one()
        items = self._session.exec(base_stmt.limit(limit).offset(offset)).all()
        return items, total

    # ------------------------------------------------------------------ 艺术家
    def list_artists(
        self, *, q: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[models.Artist], int]:
        stmt = select(models.Artist)
        if q:
            stmt = stmt.where(models.Artist.name.like(f"%{q}%"))
        stmt = stmt.order_by(models.Artist.name)
        return self._paginate(stmt, limit=limit, offset=offset)

    def get_artist(self, artist_id: str) -> models.Artist | None:
        return self._session.get(models.Artist, artist_id)

    # ------------------------------------------------------------------ 专辑
    def list_albums(
        self,
        *,
        q: str | None = None,
        artist_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[models.Album], int]:
        stmt = select(models.Album)
        if q:
            stmt = stmt.where(models.Album.name.like(f"%{q}%"))
        if artist_id:
            stmt = stmt.where(models.Album.artist_id == artist_id)
        stmt = stmt.order_by(models.Album.name)
        return self._paginate(stmt, limit=limit, offset=offset)

    def get_album(self, album_id: str) -> models.Album | None:
        return self._session.get(models.Album, album_id)

    # ------------------------------------------------------------------ 歌曲
    def list_songs(
        self,
        *,
        q: str | None = None,
        album_id: str | None = None,
        artist_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[models.Song], int]:
        stmt = select(models.Song)
        if q:
            stmt = stmt.where(models.Song.title.like(f"%{q}%"))
        if album_id:
            stmt = stmt.where(models.Song.album_id == album_id)
        if artist_id:
            stmt = stmt.where(models.Song.artist_id == artist_id)
        stmt = stmt.order_by(models.Song.title)
        return self._paginate(stmt, limit=limit, offset=offset)

    def get_song(self, song_id: str) -> models.Song | None:
        return self._session.get(models.Song, song_id)

    # ------------------------------------------------------------------ 同步状态
    def latest_sync_state(self) -> models.SyncState | None:
        stmt = select(models.SyncState).order_by(models.SyncState.started_at.desc())
        return self._session.exec(stmt).first()

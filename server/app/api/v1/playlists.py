"""歌单接口（查看 AI 创建的歌单、删除）。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
from sqlmodel import select

from app.api.deps import PlaylistServiceDep, SessionDep
from app.database.models import Song
from app.schemas.library import SongOut
from pydantic import BaseModel

router = APIRouter(prefix="/playlists", tags=["playlists"])


class PlaylistOut(BaseModel):
    id: int
    subsonic_id: str
    name: str
    description: str | None = None
    source: str
    query: str | None = None
    song_count: int
    duration: int
    created_at: str


class PlaylistDetailOut(PlaylistOut):
    songs: list[SongOut]


@router.get("", response_model=list[PlaylistOut], summary="歌单列表")
async def list_playlists(
    playlist_service: PlaylistServiceDep, session: SessionDep
) -> list[PlaylistOut]:
    records = playlist_service.list(session)
    return [_to_out(r) for r in records]


@router.get(
    "/{playlist_id}",
    response_model=PlaylistDetailOut,
    summary="歌单详情（含歌曲）",
)
async def get_playlist(
    playlist_id: int, playlist_service: PlaylistServiceDep, session: SessionDep
) -> PlaylistDetailOut:
    record = playlist_service.get(session, playlist_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="歌单不存在")
    songs: list[SongOut] = []
    if record.song_ids:
        rows = session.exec(
            select(Song).where(Song.id.in_(record.song_ids))
        ).all()
        songs = [SongOut.model_validate(r) for r in rows]
    out = _to_out(record)
    return PlaylistDetailOut(**out.model_dump(), songs=songs)


@router.delete(
    "/{playlist_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="删除歌单（Subsonic + 本地）",
)
async def delete_playlist(
    playlist_id: int, playlist_service: PlaylistServiceDep, session: SessionDep
) -> Response:
    deleted = await playlist_service.delete(session, playlist_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="歌单不存在")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _to_out(record) -> PlaylistOut:
    return PlaylistOut(
        id=record.id,
        subsonic_id=record.subsonic_id,
        name=record.name,
        description=record.description,
        source=record.source,
        query=record.query,
        song_count=record.song_count,
        duration=record.duration,
        created_at=record.created_at.isoformat() if record.created_at else "",
    )

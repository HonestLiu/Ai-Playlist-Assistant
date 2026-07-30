"""专辑浏览接口。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import BrowseServiceDep
from app.schemas.library import AlbumDetailOut, AlbumListOut, AlbumOut, SongOut

router = APIRouter(prefix="/albums", tags=["albums"])


@router.get("", response_model=AlbumListOut, summary="专辑列表（支持搜索/按艺术家过滤/分页）")
def list_albums(
    browse: BrowseServiceDep,
    q: str | None = Query(None, description="按名称模糊搜索"),
    artist_id: str | None = Query(None, description="限定某艺术家"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> AlbumListOut:
    items, total = browse.list_albums(q=q, artist_id=artist_id, limit=limit, offset=offset)
    return AlbumListOut(
        items=[AlbumOut.model_validate(a) for a in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{album_id}", response_model=AlbumDetailOut, summary="专辑详情 + 歌曲")
def get_album(album_id: str, browse: BrowseServiceDep) -> AlbumDetailOut:
    album = browse.get_album(album_id)
    if album is None:
        raise HTTPException(status_code=404, detail="专辑不存在")
    songs, _ = browse.list_songs(album_id=album_id, limit=500, offset=0)
    detail = AlbumDetailOut.model_validate(album)
    detail.songs = [SongOut.model_validate(s) for s in songs]
    return detail

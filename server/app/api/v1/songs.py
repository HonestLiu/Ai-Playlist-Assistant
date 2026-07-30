"""歌曲浏览接口。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import BrowseServiceDep
from app.schemas.library import SongListOut, SongOut

router = APIRouter(prefix="/songs", tags=["songs"])


@router.get("", response_model=SongListOut, summary="歌曲列表（支持搜索/按专辑或艺术家过滤/分页）")
def list_songs(
    browse: BrowseServiceDep,
    q: str | None = Query(None, description="按标题模糊搜索"),
    album_id: str | None = Query(None, description="限定某专辑"),
    artist_id: str | None = Query(None, description="限定某艺术家"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> SongListOut:
    items, total = browse.list_songs(
        q=q, album_id=album_id, artist_id=artist_id, limit=limit, offset=offset
    )
    return SongListOut(
        items=[SongOut.model_validate(s) for s in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{song_id}", response_model=SongOut, summary="歌曲详情")
def get_song(song_id: str, browse: BrowseServiceDep) -> SongOut:
    song = browse.get_song(song_id)
    if song is None:
        raise HTTPException(status_code=404, detail="歌曲不存在")
    return SongOut.model_validate(song)

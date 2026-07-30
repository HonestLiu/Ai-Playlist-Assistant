"""艺术家浏览接口。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import BrowseServiceDep
from app.schemas.library import AlbumOut, ArtistDetailOut, ArtistListOut, ArtistOut

router = APIRouter(prefix="/artists", tags=["artists"])


@router.get("", response_model=ArtistListOut, summary="艺术家列表（支持搜索/分页）")
def list_artists(
    browse: BrowseServiceDep,
    q: str | None = Query(None, description="按名称模糊搜索"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> ArtistListOut:
    items, total = browse.list_artists(q=q, limit=limit, offset=offset)
    return ArtistListOut(
        items=[ArtistOut.model_validate(a) for a in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{artist_id}", response_model=ArtistDetailOut, summary="艺术家详情 + 专辑")
def get_artist(artist_id: str, browse: BrowseServiceDep) -> ArtistDetailOut:
    artist = browse.get_artist(artist_id)
    if artist is None:
        raise HTTPException(status_code=404, detail="艺术家不存在")
    albums, _ = browse.list_albums(artist_id=artist_id, limit=200, offset=0)
    detail = ArtistDetailOut.model_validate(artist)
    detail.albums = [AlbumOut.model_validate(a) for a in albums]
    return detail

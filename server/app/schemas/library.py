"""音乐库相关 API 的响应模型。

与数据库表解耦：前端只看到这里定义的字段，未来表结构变了也不影响契约。
所有模型都 ``from_attributes=True``，可直接从 SQLModel 行实例化。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ArtistOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    album_count: Optional[int] = None
    song_count: Optional[int] = None
    cover_art: Optional[str] = None


class AlbumOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    artist_id: Optional[str] = None
    artist_name: Optional[str] = None
    cover_art: Optional[str] = None
    song_count: Optional[int] = None
    duration: Optional[int] = None
    year: Optional[int] = None
    genre: Optional[str] = None


class SongOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    album_id: Optional[str] = None
    album_name: Optional[str] = None
    artist_id: Optional[str] = None
    artist_name: Optional[str] = None
    track: Optional[int] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    duration: Optional[int] = None
    bit_rate: Optional[int] = None
    size: Optional[int] = None
    content_type: Optional[str] = None
    suffix: Optional[str] = None
    path: Optional[str] = None
    cover_art: Optional[str] = None


class ArtistDetailOut(ArtistOut):
    albums: list[AlbumOut] = []


class AlbumDetailOut(AlbumOut):
    songs: list[SongOut] = []


class SyncStateOut(BaseModel):
    model_config = {"from_attributes": True}

    id: Optional[int] = None
    scope: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    artists_synced: int = 0
    albums_synced: int = 0
    songs_synced: int = 0
    error: Optional[str] = None


class ArtistListOut(BaseModel):
    items: list[ArtistOut]
    total: int
    limit: int
    offset: int


class AlbumListOut(BaseModel):
    items: list[AlbumOut]
    total: int
    limit: int
    offset: int


class SongListOut(BaseModel):
    items: list[SongOut]
    total: int
    limit: int
    offset: int

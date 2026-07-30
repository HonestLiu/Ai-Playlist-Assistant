"""音乐库管理工具（去重 / 信息缺失扫描 等）的响应模型。

与数据库表解耦：前端只看到这里定义的字段，未来表结构变了也不影响契约。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ------------------------------------------------------------------ 重复歌曲
class DuplicateSongOut(BaseModel):
    """重复检测里的一首歌曲（含去重判断所需的最小字段）。"""

    model_config = {"from_attributes": True}

    id: str
    title: str
    artist_name: Optional[str] = None
    album_name: Optional[str] = None
    album_id: Optional[str] = None
    duration: Optional[int] = None
    bit_rate: Optional[int] = None
    size: Optional[int] = None
    path: Optional[str] = None
    cover_art: Optional[str] = None


class DuplicateGroupOut(BaseModel):
    """一组疑似重复：``kept`` 是建议保留的那首，``duplicates`` 是可清理的副本。"""

    key: str = Field(description="归一化后的「标题 · 艺术家」标识")
    title: str
    artist: str
    kept: DuplicateSongOut
    duplicates: list[DuplicateSongOut] = Field(default_factory=list)
    reason: str = Field(description="判定为重复的依据说明")


class DuplicateReportOut(BaseModel):
    total_songs: int = Field(description="本地歌曲总数")
    groups: list[DuplicateGroupOut] = Field(default_factory=list)
    removable_count: int = Field(description="建议可清理的副本总数")
    scanned_at: datetime


class DeleteFailure(BaseModel):
    id: str
    error: str


class DeleteDuplicatesRequest(BaseModel):
    song_ids: list[str] = Field(min_length=1, description="要删除的歌曲 id 列表")


class PlaylistCleanRequest(BaseModel):
    subsonic_id: str = Field(description="Subsonic 侧歌单 id")


class DeleteResultOut(BaseModel):
    requested: int
    deleted: int
    failed: list[DeleteFailure] = Field(default_factory=list)


# ------------------------------------------------------------------ 歌单去重
class PlaylistDuplicateEntry(BaseModel):
    """歌单里重复出现的一首歌（按 song_id 或 标题+艺术家 判定）。"""

    song_id: str
    title: str
    artist: str
    occurrences: int = Field(description="在歌单里出现的次数")


class PlaylistDuplicateOut(BaseModel):
    playlist_id: str = Field(description="本地歌单记录 id")
    subsonic_id: str = Field(description="Subsonic 侧歌单 id")
    name: str
    source: str
    song_count: int
    unique_count: int = Field(description="去重后保留的歌曲数")
    duplicates: list[PlaylistDuplicateEntry] = Field(default_factory=list)


class PlaylistDuplicateReportOut(BaseModel):
    playlists: list[PlaylistDuplicateOut] = Field(default_factory=list)
    playlists_with_duplicates: int = 0
    total_removable: int = 0


class PlaylistCleanResultOut(BaseModel):
    playlist_id: str
    name: str
    removed: int = Field(description="本次移除的重复条目数")
    new_count: int = Field(description="去重后歌单歌曲数")


# ------------------------------------------------------------------ 信息缺失扫描
class MetadataGapOut(BaseModel):
    category: str
    label: str
    count: int
    samples: list[DuplicateSongOut] = Field(default_factory=list)


class MetadataGapReportOut(BaseModel):
    total_songs: int
    gaps: list[MetadataGapOut] = Field(default_factory=list)
    scanned_at: datetime

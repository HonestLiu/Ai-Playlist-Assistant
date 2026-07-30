"""数据库表定义（SQLModel + SQLite）。

Phase 2 先落地 SQLite；迁移 PostgreSQL 时只需换 engine，这里所有表都用
SQLModel 标准字段，不依赖 SQLite 特有类型。

设计要点：
- 三张实体表（artists / albums / songs）以 Subsonic 的 ID 为主键，天然幂等 upsert。
- ``synced_at`` 记录写入时间，为未来「增量同步」预留钩子（服务器支持时才用）。
- 所有「可能为空」的字段全部 ``Optional``，兼容 zmusicv2 大量返回 null 的情况。
- 常用过滤/排序字段建索引（name / artist / year / genre），支撑浏览与未来 AI 筛选。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Artist(SQLModel, table=True):
    __tablename__ = "artists"

    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    album_count: Optional[int] = None
    song_count: Optional[int] = None
    cover_art: Optional[str] = None
    music_folder_id: Optional[int] = Field(default=None, index=True)
    synced_at: Optional[datetime] = Field(default=None, index=True)


class Album(SQLModel, table=True):
    __tablename__ = "albums"

    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    artist_id: Optional[str] = Field(default=None, index=True)
    artist_name: Optional[str] = Field(default=None, index=True)
    cover_art: Optional[str] = None
    song_count: Optional[int] = None
    duration: Optional[int] = None
    year: Optional[int] = Field(default=None, index=True)
    genre: Optional[str] = Field(default=None, index=True)
    music_folder_id: Optional[int] = Field(default=None, index=True)
    synced_at: Optional[datetime] = Field(default=None, index=True)


class Song(SQLModel, table=True):
    __tablename__ = "songs"

    id: str = Field(primary_key=True)
    title: str = Field(index=True)
    album_id: Optional[str] = Field(default=None, index=True)
    album_name: Optional[str] = Field(default=None, index=True)
    artist_id: Optional[str] = Field(default=None, index=True)
    artist_name: Optional[str] = Field(default=None, index=True)
    track: Optional[int] = None
    year: Optional[int] = Field(default=None, index=True)
    genre: Optional[str] = Field(default=None, index=True)
    duration: Optional[int] = None
    bit_rate: Optional[int] = None
    size: Optional[int] = None
    content_type: Optional[str] = None
    suffix: Optional[str] = None
    path: Optional[str] = None
    cover_art: Optional[str] = None
    music_folder_id: Optional[int] = Field(default=None, index=True)
    synced_at: Optional[datetime] = Field(default=None, index=True)


class SyncState(SQLModel, table=True):
    """一次同步任务的运行记录（最新一条即当前状态）。"""

    __tablename__ = "sync_state"

    id: Optional[int] = Field(default=None, primary_key=True)
    scope: str = Field(index=True)
    status: str
    started_at: datetime = Field(default_factory=_now)
    finished_at: Optional[datetime] = None
    artists_synced: int = 0
    albums_synced: int = 0
    songs_synced: int = 0
    error: Optional[str] = None


class Playlist(SQLModel, table=True):
    """本地记录的 AI 创建的歌单（Subsonic 侧另存一份，二者通过 subsonic_id 关联）。"""

    __tablename__ = "playlists"

    id: Optional[int] = Field(default=None, primary_key=True)
    subsonic_id: str = Field(index=True)
    name: str = Field(index=True)
    description: str | None = None
    source: str = Field(default="ai", index=True)  # ai / daily_mix / manual
    query: str | None = None  # 来源的自然语言需求
    song_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    song_count: int = 0
    duration: int = 0
    created_at: datetime = Field(default_factory=_now, index=True)

"""Subsonic 音乐库领域模型（客户端输出）。

这些模型是 ``SubsonicClient`` 把 Subsonic 原始 JSON 解析后交出的产物。
业务代码只消费这里的字段，不感知 Subsonic 响应里的 camelCase 键名、
``subsonic-response`` 包裹结构或 folder ID 之类的协议细节。

所有字段都按「服务器可能不返回」来设计，可空即空。
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class MusicFolder(BaseModel):
    """音乐库根目录（getMusicFolders 返回）。"""

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str


class SubsonicArtist(BaseModel):
    """艺术家（来自 getArtists / getArtist）。"""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    album_count: Optional[int] = None
    song_count: Optional[int] = None
    cover_art: Optional[str] = None


class SubsonicAlbum(BaseModel):
    """专辑（来自 getArtist / getAlbum / getAlbumList2）。"""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    artist_id: Optional[str] = None
    artist_name: Optional[str] = None
    cover_art: Optional[str] = None
    song_count: Optional[int] = None
    duration: Optional[int] = None
    year: Optional[int] = None
    genre: Optional[str] = None


class SubsonicSong(BaseModel):
    """歌曲（来自 getAlbum / getSong）。"""

    model_config = ConfigDict(extra="ignore")

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

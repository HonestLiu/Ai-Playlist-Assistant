"""Subsonic 相关的领域模型（与 HTTP 传输结构无关）。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SubsonicConnectionConfig(BaseModel):
    """一次 Subsonic 连接所需的全部信息。

    这是 ``SubsonicClient`` 的唯一入参来源——client 不认识 Settings，
    也不认识运行时配置存储，只认识这个值对象，方便测试与复用。
    """

    url: str
    username: str
    password: str
    client_name: str = "ai-playlist"
    api_version: str = "1.16.1"
    legacy_auth: bool = False
    timeout: float = 15.0
    verify_ssl: bool = True

    @field_validator("url")
    @classmethod
    def _normalize_url(cls, value: str) -> str:
        return value.strip().rstrip("/")

    @property
    def is_complete(self) -> bool:
        return bool(self.url and self.username and self.password)

    @property
    def rest_base_url(self) -> str:
        """Subsonic 的 REST 根路径固定为 ``<server>/rest``。"""

        base = self.url
        return base if base.endswith("/rest") else f"{base}/rest"


class SubsonicServerInfo(BaseModel):
    """服务器自报的信息。"""

    version: str | None = None
    server_type: str | None = None
    server_version: str | None = None
    open_subsonic: bool = False


class ConnectionStatus(BaseModel):
    """连接体检结果，直接给前端展示。"""

    configured: bool = Field(description="是否已经填好地址/账号/密码")
    connected: bool = Field(description="本次探测是否连通")
    url: str | None = None
    username: str | None = None
    server: SubsonicServerInfo | None = None
    latency_ms: int | None = None
    error_code: str | None = None
    error_message: str | None = None
    checked_at: datetime = Field(default_factory=datetime.now)


class SubsonicPlaylist(BaseModel):
    """歌单（已脱离 Subsonic 的传输结构，统一成自己的模型）。"""

    id: str
    name: str = ""
    comment: str | None = None
    owner: str | None = None
    public: bool = False
    song_count: int = 0
    duration: int = 0
    cover_art: str | None = None
    song_ids: list[str] = Field(default_factory=list)
    created: datetime | None = None
    changed: datetime | None = None

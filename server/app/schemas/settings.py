"""设置相关的 API 传输结构。密码只进不出。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SubsonicConfigIn(BaseModel):
    """前端提交的 Subsonic 连接配置。"""

    url: str = Field(min_length=1, examples=["https://music.example.com"])
    username: str = Field(min_length=1)
    password: str | None = Field(
        default=None,
        description="留空表示沿用已保存的密码",
    )
    legacy_auth: bool = False
    verify_ssl: bool = True


class SubsonicConfigOut(BaseModel):
    """回显给前端的配置，密码永远不返回。"""

    url: str
    username: str
    has_password: bool
    legacy_auth: bool
    verify_ssl: bool
    source: str = Field(description="env = 来自 .env，runtime = 来自网页保存的覆盖值")
    configured: bool


class LLMConfigIn(BaseModel):
    """前端提交的 LLM 配置。"""

    provider: str = Field(default="openai", examples=["openai", "mock"])
    base_url: str = Field(default="", description="OpenAI 兼容接口的 base_url，留空用默认")
    api_key: str | None = Field(default=None, description="留空表示沿用已保存的值")
    model: str = Field(default="", description="模型名，留空用默认")
    temperature: float | None = None


class LLMConfigOut(BaseModel):
    """回显给前端的 LLM 配置，api_key 永远不返回。"""

    provider: str
    base_url: str
    has_api_key: bool
    model: str
    temperature: float | None = None
    source: str


class LLMTestResult(BaseModel):
    """LLM 连接测试结果。"""

    provider: str
    ok: bool
    model: str | None = None
    error: str | None = None


class PreferencesIn(BaseModel):
    """前端提交的用户偏好（全部可选，缺省表示不改动）。"""

    playlist_title_prefix: bool | None = Field(
        default=None,
        description="AI 生成的歌单标题是否保留「AI · 」前缀，默认 true",
    )


class PreferencesOut(BaseModel):
    """回显给前端的用户偏好。"""

    playlist_title_prefix: bool = Field(
        default=True,
        description="AI 生成的歌单标题是否保留「AI · 」前缀",
    )


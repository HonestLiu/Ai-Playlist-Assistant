"""集中式配置。

约定：进程内任何地方都通过 ``get_settings()`` 拿配置，禁止直接读 ``os.environ``。
嵌套配置用 ``SECTION__FIELD`` 形式的环境变量覆盖，例如 ``SUBSONIC__URL``。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# server/ 目录
BASE_DIR = Path(__file__).resolve().parents[2]


class ServerSettings(BaseModel):
    """HTTP 服务自身的运行参数。"""

    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    # NoDecode：环境变量里写逗号分隔字符串，不要求写成 JSON 数组
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("log_level")
    @classmethod
    def _upper(cls, value: str) -> str:
        return value.upper()


class SubsonicSettings(BaseModel):
    """Subsonic 服务器连接参数的默认值（可被运行时配置覆盖）。"""

    url: str = ""
    username: str = ""
    password: SecretStr = SecretStr("")
    client_name: str = "ai-playlist"
    api_version: str = "1.16.1"
    legacy_auth: bool = False
    timeout: float = 15.0
    verify_ssl: bool = True


class LLMSettings(BaseModel):
    """LLM 参数。Phase 3 才会真正使用，这里先把位置留好。"""

    provider: str = "openai"
    base_url: str = "https://api.openai.com/v1"
    api_key: SecretStr = SecretStr("")
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int | None = None


class Settings(BaseSettings):
    """应用总配置。"""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app_name: str = "AI Playlist Assistant"
    api_prefix: str = "/api/v1"
    debug: bool = False

    server: ServerSettings = Field(default_factory=ServerSettings)
    subsonic: SubsonicSettings = Field(default_factory=SubsonicSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)

    @property
    def base_dir(self) -> Path:
        return BASE_DIR

    @property
    def data_dir(self) -> Path:
        path = BASE_DIR / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """全局单例。测试里可用 ``get_settings.cache_clear()`` 重置。"""

    return Settings()

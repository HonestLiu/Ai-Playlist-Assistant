"""Subsonic 连接配置的解析与持久化。

优先级：运行时覆盖值（网页保存）> .env 默认值。
上层只跟 ``SubsonicConnectionConfig`` 这个值对象打交道。
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.logging import get_logger
from app.database.config_store import ConfigStore
from app.models.subsonic import SubsonicConnectionConfig
from app.schemas.settings import SubsonicConfigIn, SubsonicConfigOut

logger = get_logger(__name__)

SOURCE_ENV = "env"
SOURCE_RUNTIME = "runtime"


class SubsonicSettingsService:
    def __init__(self, settings: Settings, store: ConfigStore) -> None:
        self._settings = settings
        self._store = store

    # ------------------------------------------------------------------ 读取
    def _env_config(self) -> SubsonicConnectionConfig:
        env = self._settings.subsonic
        return SubsonicConnectionConfig(
            url=env.url,
            username=env.username,
            password=env.password.get_secret_value(),
            client_name=env.client_name,
            api_version=env.api_version,
            legacy_auth=env.legacy_auth,
            timeout=env.timeout,
            verify_ssl=env.verify_ssl,
        )

    def resolve(self) -> SubsonicConnectionConfig:
        """得到当前生效的连接配置。"""

        config = self._env_config()
        override = self._store.get_subsonic()
        if not override:
            return config
        merged = config.model_dump()
        merged.update({k: v for k, v in override.items() if v is not None})
        return SubsonicConnectionConfig(**merged)

    def current_source(self) -> str:
        return SOURCE_RUNTIME if self._store.get_subsonic() else SOURCE_ENV

    def to_view(self) -> SubsonicConfigOut:
        config = self.resolve()
        return SubsonicConfigOut(
            url=config.url,
            username=config.username,
            has_password=bool(config.password),
            legacy_auth=config.legacy_auth,
            verify_ssl=config.verify_ssl,
            source=self.current_source(),
            configured=config.is_complete,
        )

    # ------------------------------------------------------------------ 写入
    def build_candidate(self, payload: SubsonicConfigIn) -> SubsonicConnectionConfig:
        """把前端提交的内容合成一份完整配置（不落盘），用于「测试连接」。"""

        base = self.resolve()
        return SubsonicConnectionConfig(
            url=payload.url,
            username=payload.username,
            password=payload.password if payload.password else base.password,
            client_name=base.client_name,
            api_version=base.api_version,
            legacy_auth=payload.legacy_auth,
            timeout=base.timeout,
            verify_ssl=payload.verify_ssl,
        )

    def save(self, payload: SubsonicConfigIn) -> SubsonicConnectionConfig:
        config = self.build_candidate(payload)
        self._store.set_subsonic(
            {
                "url": config.url,
                "username": config.username,
                "password": config.password,
                "legacy_auth": config.legacy_auth,
                "verify_ssl": config.verify_ssl,
            }
        )
        logger.info("已保存 Subsonic 运行时配置: %s@%s", config.username, config.url)
        return config

    def reset(self) -> None:
        self._store.clear_subsonic()
        logger.info("已清除 Subsonic 运行时配置，回落到 .env")

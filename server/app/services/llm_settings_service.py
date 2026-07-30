"""LLM 配置的解析与持久化（镜像 SubsonicSettingsService）。

优先级：运行时覆盖值（网页保存）> .env 默认值。上层只跟 ``LLMSettings``
这个值对象打交道；provider 工厂据此实例化具体 Provider。
"""

from __future__ import annotations

from app.core.config import LLMSettings, Settings
from app.core.logging import get_logger
from app.database.config_store import ConfigStore
from app.schemas.settings import LLMConfigIn, LLMConfigOut

logger = get_logger(__name__)

SOURCE_ENV = "env"
SOURCE_RUNTIME = "runtime"


class LLMSettingsService:
    def __init__(self, settings: Settings, store: ConfigStore) -> None:
        self._settings = settings
        self._store = store

    # ------------------------------------------------------------------ 读取
    def resolve(self) -> LLMSettings:
        """得到当前生效的 LLM 配置（运行时覆盖优先）。"""

        base = self._settings.llm
        override = self._store.get_llm()
        if not override:
            return base
        merged = base.model_dump()
        for key, value in override.items():
            if value is not None:
                merged[key] = value
        return LLMSettings(**merged)

    def current_source(self) -> str:
        return SOURCE_RUNTIME if self._store.get_llm() else SOURCE_ENV

    def to_view(self) -> LLMConfigOut:
        cfg = self.resolve()
        return LLMConfigOut(
            provider=cfg.provider,
            base_url=cfg.base_url,
            has_api_key=bool(cfg.api_key and cfg.api_key.get_secret_value()),
            model=cfg.model,
            temperature=cfg.temperature,
            source=self.current_source(),
        )

    # ------------------------------------------------------------------ 写入
    def build_candidate(self, payload: LLMConfigIn) -> LLMSettings:
        base = self.resolve()
        return LLMSettings(
            provider=payload.provider or base.provider,
            base_url=payload.base_url or base.base_url,
            api_key=payload.api_key or base.api_key,
            model=payload.model or base.model,
            temperature=payload.temperature
            if payload.temperature is not None
            else base.temperature,
            max_tokens=base.max_tokens,
        )

    def save(self, payload: LLMConfigIn) -> LLMSettings:
        config = self.build_candidate(payload)
        self._store.set_llm(
            {
                "provider": config.provider,
                "base_url": config.base_url,
                "api_key": config.api_key.get_secret_value() if config.api_key else "",
                "model": config.model,
                "temperature": config.temperature,
            }
        )
        logger.info("已保存 LLM 运行时配置: provider=%s model=%s", config.provider, config.model)
        return config

    def reset(self) -> None:
        self._store.clear_llm()
        logger.info("已清除 LLM 运行时配置，回落到 .env")

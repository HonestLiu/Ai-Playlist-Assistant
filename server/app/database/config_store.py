"""运行时配置存储。

Phase 1 用 JSON 文件落盘，够用且零依赖。抽象成 ``ConfigStore`` 接口，
Phase 2 引入 SQLModel 后只要在本包内加一个 ``SqlConfigStore`` 实现，
上层 service 和 api 一行都不用改。
"""

from __future__ import annotations

import json
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

_SUBSONIC_KEY = "subsonic"
_LLM_KEY = "llm"


class ConfigStore(ABC):
    """运行时可变配置的读写接口。"""

    @abstractmethod
    def get(self, section: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def set(self, section: str, value: dict[str, Any]) -> None: ...

    @abstractmethod
    def delete(self, section: str) -> None: ...

    # -- 语义化封装，避免上层到处写魔法字符串 --
    def get_subsonic(self) -> dict[str, Any] | None:
        return self.get(_SUBSONIC_KEY)

    def set_subsonic(self, value: dict[str, Any]) -> None:
        self.set(_SUBSONIC_KEY, value)

    def clear_subsonic(self) -> None:
        self.delete(_SUBSONIC_KEY)

    # -- LLM 配置（镜像 subsonic） --
    def get_llm(self) -> dict[str, Any] | None:
        return self.get(_LLM_KEY)

    def set_llm(self, value: dict[str, Any]) -> None:
        self.set(_LLM_KEY, value)

    def clear_llm(self) -> None:
        self.delete(_LLM_KEY)


class JsonFileConfigStore(ConfigStore):
    """单文件 JSON 实现，进程内加锁，够 Phase 1 的单用户场景使用。"""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._cache: dict[str, Any] | None = None

    def _load(self) -> dict[str, Any]:
        if self._cache is not None:
            return self._cache
        if not self._path.exists():
            self._cache = {}
            return self._cache
        try:
            self._cache = json.loads(self._path.read_text("utf-8")) or {}
        except (OSError, json.JSONDecodeError):
            logger.warning("运行时配置文件损坏，已忽略: %s", self._path)
            self._cache = {}
        return self._cache

    def _flush(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
        tmp.replace(self._path)
        self._cache = data

    def get(self, section: str) -> dict[str, Any] | None:
        with self._lock:
            value = self._load().get(section)
            return dict(value) if isinstance(value, dict) else None

    def set(self, section: str, value: dict[str, Any]) -> None:
        with self._lock:
            data = dict(self._load())
            data[section] = value
            self._flush(data)

    def delete(self, section: str) -> None:
        with self._lock:
            data = dict(self._load())
            if data.pop(section, None) is not None:
                self._flush(data)

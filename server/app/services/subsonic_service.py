"""Subsonic 用例层。

职责是「编排」：拿配置、开 client、把异常翻译成业务结果。
它不关心 HTTP 细节，也不关心配置存在哪儿。
"""

from __future__ import annotations

import time

from app.core.logging import get_logger
from app.models.subsonic import ConnectionStatus, SubsonicConnectionConfig
from app.services.settings_service import SubsonicSettingsService
from app.subsonic.client import SubsonicClient
from app.subsonic.exceptions import SubsonicError

logger = get_logger(__name__)


class SubsonicService:
    def __init__(self, settings_service: SubsonicSettingsService) -> None:
        self._settings_service = settings_service

    def _client(self, config: SubsonicConnectionConfig) -> SubsonicClient:
        return SubsonicClient(config)

    async def check(self, config: SubsonicConnectionConfig | None = None) -> ConnectionStatus:
        """对给定配置（默认取当前生效配置）做一次连通性体检。

        注意：这里**不抛异常**，失败也返回结构化状态，因为「连不上」
        对前端来说是正常的展示分支，不是接口错误。
        """

        config = config or self._settings_service.resolve()
        if not config.is_complete:
            return ConnectionStatus(
                configured=False,
                connected=False,
                url=config.url or None,
                username=config.username or None,
                error_code="subsonic_not_configured",
                error_message="尚未填写服务器地址、用户名或密码",
            )

        started = time.perf_counter()
        try:
            async with self._client(config) as client:
                server = await client.ping()
        except SubsonicError as exc:
            logger.warning("Subsonic 连接失败 [%s]: %s", exc.code, exc.message)
            return ConnectionStatus(
                configured=True,
                connected=False,
                url=config.url,
                username=config.username,
                error_code=exc.code,
                error_message=exc.message,
            )

        latency = int((time.perf_counter() - started) * 1000)
        return ConnectionStatus(
            configured=True,
            connected=True,
            url=config.url,
            username=config.username,
            server=server,
            latency_ms=latency,
        )

"""统一异常体系。

所有对外可见的失败都必须是 ``AppError`` 的子类，FastAPI 层把它翻译成
``{"code": ..., "message": ..., "detail": ...}``，前端只需要认这一种结构。
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """业务异常基类。"""

    code: str = "internal_error"
    status_code: int = 500
    message: str = "服务内部错误"

    def __init__(
        self,
        message: str | None = None,
        *,
        detail: Any = None,
        code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        self.message = message or self.message
        self.detail = detail
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)

    def to_payload(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "detail": self.detail}


class ConfigurationError(AppError):
    """配置缺失或非法，例如还没填 Subsonic 地址。"""

    code = "configuration_error"
    status_code = 400
    message = "配置不完整或不合法"


class NotFoundError(AppError):
    code = "not_found"
    status_code = 404
    message = "资源不存在"


class UpstreamError(AppError):
    """依赖的外部服务出问题（Subsonic / LLM 等）。"""

    code = "upstream_error"
    status_code = 502
    message = "上游服务异常"

"""通用 API 传输结构。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """所有失败响应的统一结构。"""

    code: str = Field(examples=["subsonic_auth_failed"])
    message: str
    detail: Any = None


class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str
    version: str
    debug: bool

"""认证与启动引导的 API 传输结构。密码只进不出。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.security import MIN_PASSWORD_LENGTH


class UserOut(BaseModel):
    """当前登录用户。"""

    id: int
    username: str
    is_admin: bool
    created_at: datetime


class LoginIn(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    remember: bool = Field(default=True, description="关闭浏览器后是否保持登录")


class BootstrapIn(BaseModel):
    """创建首个管理员账号。仅在系统尚无任何用户时允许调用。"""

    username: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)


class ChangePasswordIn(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)


class SessionOut(BaseModel):
    """前端鉴权网关的唯一数据源：一次请求拿全所有分支所需状态。"""

    auth_enabled: bool = Field(description="False 表示后端关闭了鉴权，前端直接放行")
    needs_bootstrap: bool = Field(description="尚无任何账号，应进入启动引导第一步")
    authenticated: bool
    user: UserOut | None = None
    onboarding_completed: bool = Field(description="启动引导是否已走完")


class SetupStatusOut(BaseModel):
    """启动引导每一步的完成情况。"""

    needs_bootstrap: bool
    account_ready: bool
    subsonic_configured: bool
    subsonic_connected: bool | None = Field(
        default=None, description="None 表示未配置或未探测"
    )
    llm_configured: bool
    llm_provider: str
    library_synced: bool
    song_count: int
    completed: bool

"""登录校验相关接口。

会话用 HttpOnly Cookie 承载：``<audio src="/api/v1/stream/...">`` 与封面 ``<img>``
由浏览器直接发起，没法带 Authorization header，只有 cookie 能一并覆盖。
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response, status

from app.api.deps import (
    AuthServiceDep,
    ConfigStoreDep,
    CurrentUserDep,
    RequireUserDep,
    SessionDep,
    SessionTokenDep,
    SettingsDep,
)
from app.core.config import Settings
from app.database.models import AppUser
from app.schemas.auth import (
    BootstrapIn,
    ChangePasswordIn,
    LoginIn,
    SessionOut,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_user_out(user: AppUser) -> UserOut:
    return UserOut(
        id=user.id or 0,
        username=user.username,
        is_admin=user.is_admin,
        created_at=user.created_at,
    )


def _set_session_cookie(
    response: Response, settings: Settings, token: str, *, remember: bool = True
) -> None:
    auth = settings.auth
    response.set_cookie(
        key=auth.cookie_name,
        value=token,
        # 不勾选「记住我」时用会话 cookie（关掉浏览器即失效）
        max_age=auth.session_ttl_hours * 3600 if remember else None,
        httponly=True,
        secure=auth.cookie_secure,
        samesite=auth.cookie_samesite,  # type: ignore[arg-type]
        path="/",
    )


def _clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(settings.auth.cookie_name, path="/")


@router.get("/session", response_model=SessionOut, summary="当前会话状态")
async def read_session(
    user: CurrentUserDep,
    session: SessionDep,
    auth_service: AuthServiceDep,
    settings: SettingsDep,
    store: ConfigStoreDep,
) -> SessionOut:
    """前端鉴权网关的唯一入口，一次请求决定去登录页、引导页还是主界面。"""

    needs_bootstrap = auth_service.needs_bootstrap(session)
    return SessionOut(
        auth_enabled=settings.auth.enabled,
        needs_bootstrap=needs_bootstrap,
        authenticated=user is not None or not settings.auth.enabled,
        user=_to_user_out(user) if user else None,
        onboarding_completed=store.is_onboarding_completed(),
    )


@router.post(
    "/bootstrap",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建首个管理员账号（仅首次可用）",
)
async def bootstrap(
    payload: BootstrapIn,
    request: Request,
    response: Response,
    session: SessionDep,
    auth_service: AuthServiceDep,
    settings: SettingsDep,
    store: ConfigStoreDep,
) -> SessionOut:
    user = auth_service.bootstrap_admin(session, payload.username, payload.password)
    token, _ = auth_service.create_session(
        session, user, user_agent=request.headers.get("user-agent")
    )
    _set_session_cookie(response, settings, token)
    return SessionOut(
        auth_enabled=settings.auth.enabled,
        needs_bootstrap=False,
        authenticated=True,
        user=_to_user_out(user),
        onboarding_completed=store.is_onboarding_completed(),
    )


@router.post("/login", response_model=SessionOut, summary="登录")
async def login(
    payload: LoginIn,
    request: Request,
    response: Response,
    session: SessionDep,
    auth_service: AuthServiceDep,
    settings: SettingsDep,
    store: ConfigStoreDep,
) -> SessionOut:
    user = auth_service.authenticate(session, payload.username, payload.password)
    token, _ = auth_service.create_session(
        session, user, user_agent=request.headers.get("user-agent")
    )
    _set_session_cookie(response, settings, token, remember=payload.remember)
    return SessionOut(
        auth_enabled=settings.auth.enabled,
        needs_bootstrap=False,
        authenticated=True,
        user=_to_user_out(user),
        onboarding_completed=store.is_onboarding_completed(),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="登出",
)
async def logout(
    token: SessionTokenDep,
    session: SessionDep,
    auth_service: AuthServiceDep,
    settings: SettingsDep,
) -> Response:
    auth_service.revoke(session, token)
    result = Response(status_code=status.HTTP_204_NO_CONTENT)
    _clear_session_cookie(result, settings)
    return result


@router.post("/password", response_model=UserOut, summary="修改密码")
async def change_password(
    payload: ChangePasswordIn,
    request: Request,
    response: Response,
    user: RequireUserDep,
    session: SessionDep,
    auth_service: AuthServiceDep,
    settings: SettingsDep,
) -> UserOut:
    """改密后所有旧会话失效，当前设备立刻换发新 cookie，不用重新登录。"""

    auth_service.change_password(
        session, user, payload.current_password, payload.new_password
    )
    token, _ = auth_service.create_session(
        session, user, user_agent=request.headers.get("user-agent")
    )
    _set_session_cookie(response, settings, token)
    return _to_user_out(user)

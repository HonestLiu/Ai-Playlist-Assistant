"""Subsonic 防腐层的异常。全部继承 AppError，方便统一翻译成 HTTP 响应。"""

from __future__ import annotations

from app.core.errors import AppError


class SubsonicError(AppError):
    code = "subsonic_error"
    status_code = 502
    message = "Subsonic 请求失败"


class SubsonicNotConfiguredError(SubsonicError):
    code = "subsonic_not_configured"
    status_code = 400
    message = "尚未配置 Subsonic 服务器地址或账号"


class SubsonicUnavailableError(SubsonicError):
    code = "subsonic_unavailable"
    status_code = 502
    message = "无法连接到 Subsonic 服务器"


class SubsonicTimeoutError(SubsonicUnavailableError):
    code = "subsonic_timeout"
    status_code = 504
    message = "连接 Subsonic 服务器超时"


class SubsonicAuthError(SubsonicError):
    code = "subsonic_auth_failed"
    status_code = 401
    message = "Subsonic 用户名或密码错误"


class SubsonicPermissionError(SubsonicError):
    """账号已通过认证，但无权执行该操作（如删除歌曲需要管理员权限）。

    对应 Subsonic 官方错误码 50（User is not authorized for the given operation）。
    """

    code = "subsonic_forbidden"
    status_code = 403
    message = "账号无权执行该操作（删除歌曲通常需要 Subsonic 管理员权限）"


class SubsonicNotFoundError(SubsonicError):
    code = "subsonic_not_found"
    status_code = 404
    message = "Subsonic 上找不到该资源"


class SubsonicResponseError(SubsonicError):
    code = "subsonic_bad_response"
    status_code = 502
    message = "Subsonic 返回了无法识别的响应"


# Subsonic 官方错误码 -> 本地异常
_ERROR_CODE_MAP: dict[int, type[SubsonicError]] = {
    0: SubsonicResponseError,
    10: SubsonicResponseError,
    20: SubsonicResponseError,
    30: SubsonicUnavailableError,
    40: SubsonicAuthError,
    41: SubsonicAuthError,
    50: SubsonicPermissionError,
    60: SubsonicAuthError,
    70: SubsonicNotFoundError,
}


def map_subsonic_error(code: int | None, message: str | None) -> SubsonicError:
    exc_cls = _ERROR_CODE_MAP.get(code or -1, SubsonicResponseError)
    return exc_cls(message or None, detail={"subsonic_code": code})

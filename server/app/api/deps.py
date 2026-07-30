"""FastAPI 依赖注入装配点。

所有对象的组装都集中在这里，路由函数只声明「我要什么」，
不负责 new 任何东西——这样换实现（比如把 JSON 存储换成数据库）只改这一处。
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request
from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.database.config_store import ConfigStore, JsonFileConfigStore
from app.database.engine import get_session
from app.database.models import AppUser
from app.services.auth_service import AuthError, AuthService
from app.services.browse_service import BrowseService
from app.services.daily_mix_service import DailyMixService
from app.services.library_sync_service import LibrarySyncService
from app.services.llm_settings_service import LLMSettingsService
from app.services.play_history_service import PlayHistoryService
from app.services.playlist_service import PlaylistService
from app.services.recommendation_service import RecommendationService
from app.services.settings_service import SubsonicSettingsService
from app.services.subsonic_service import SubsonicService

SettingsDep = Annotated[Settings, Depends(get_settings)]

SessionDep = Annotated[Session, Depends(get_session)]


@lru_cache(maxsize=1)
def _config_store_singleton() -> ConfigStore:
    return JsonFileConfigStore(get_settings().data_dir / "runtime_config.json")


def get_config_store() -> ConfigStore:
    return _config_store_singleton()


ConfigStoreDep = Annotated[ConfigStore, Depends(get_config_store)]


# ---------------------------------------------------------------- 认证
def get_auth_service(settings: SettingsDep) -> AuthService:
    return AuthService(settings.auth.session_ttl_hours)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def session_token(request: Request, settings: SettingsDep) -> str | None:
    """从 Cookie 中取出会话令牌。"""

    return request.cookies.get(settings.auth.cookie_name)


SessionTokenDep = Annotated[str | None, Depends(session_token)]


def get_current_user(
    token: SessionTokenDep,
    session: SessionDep,
    auth_service: AuthServiceDep,
    settings: SettingsDep,
) -> AppUser | None:
    """可选当前用户：鉴权关闭或未登录时为 None。"""

    if not settings.auth.enabled:
        return None
    return auth_service.resolve(session, token)


CurrentUserDep = Annotated[AppUser | None, Depends(get_current_user)]


def require_current_user(user: CurrentUserDep, settings: SettingsDep) -> AppUser:
    """强制登录。鉴权关闭时此类接口没有意义，同样拒绝。"""

    if not settings.auth.enabled:
        raise AuthError("当前部署已关闭登录校验，账号相关操作不可用", status_code=400)
    if user is None:
        raise AuthError()
    return user


RequireUserDep = Annotated[AppUser, Depends(require_current_user)]


def get_subsonic_settings_service(
    settings: SettingsDep, store: ConfigStoreDep
) -> SubsonicSettingsService:
    return SubsonicSettingsService(settings, store)


SubsonicSettingsServiceDep = Annotated[
    SubsonicSettingsService, Depends(get_subsonic_settings_service)
]


def get_subsonic_service(
    settings_service: SubsonicSettingsServiceDep,
) -> SubsonicService:
    return SubsonicService(settings_service)


SubsonicServiceDep = Annotated[SubsonicService, Depends(get_subsonic_service)]


def get_browse_service(session: SessionDep) -> BrowseService:
    return BrowseService(session)


BrowseServiceDep = Annotated[BrowseService, Depends(get_browse_service)]


def get_library_sync_service(
    settings_service: SubsonicSettingsServiceDep,
) -> LibrarySyncService:
    return LibrarySyncService(settings_service)


LibrarySyncServiceDep = Annotated[
    LibrarySyncService, Depends(get_library_sync_service)
]


def get_llm_settings_service(
    settings: SettingsDep, store: ConfigStoreDep
) -> LLMSettingsService:
    return LLMSettingsService(settings, store)


LLMSettingsServiceDep = Annotated[LLMSettingsService, Depends(get_llm_settings_service)]


def get_playlist_service(
    subsonic_settings_service: SubsonicSettingsServiceDep,
) -> PlaylistService:
    return PlaylistService(subsonic_settings_service)


PlaylistServiceDep = Annotated[PlaylistService, Depends(get_playlist_service)]


def get_play_history_service() -> PlayHistoryService:
    return PlayHistoryService()


PlayHistoryServiceDep = Annotated[PlayHistoryService, Depends(get_play_history_service)]


def get_recommendation_service(
    llm_settings_service: LLMSettingsServiceDep,
    subsonic_settings_service: SubsonicSettingsServiceDep,
) -> RecommendationService:
    return RecommendationService(llm_settings_service, subsonic_settings_service)


RecommendationServiceDep = Annotated[
    RecommendationService, Depends(get_recommendation_service)
]


def get_daily_mix_service(
    rec_service: RecommendationServiceDep,
    playlist_service: PlaylistServiceDep,
) -> DailyMixService:
    return DailyMixService(rec_service, playlist_service)


DailyMixServiceDep = Annotated[DailyMixService, Depends(get_daily_mix_service)]

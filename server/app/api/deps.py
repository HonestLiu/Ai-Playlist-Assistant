"""FastAPI 依赖注入装配点。

所有对象的组装都集中在这里，路由函数只声明「我要什么」，
不负责 new 任何东西——这样换实现（比如把 JSON 存储换成数据库）只改这一处。
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.database.config_store import ConfigStore, JsonFileConfigStore
from app.database.engine import get_session
from app.services.browse_service import BrowseService
from app.services.daily_mix_service import DailyMixService
from app.services.library_sync_service import LibrarySyncService
from app.services.llm_settings_service import LLMSettingsService
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

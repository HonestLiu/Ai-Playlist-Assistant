"""启动引导。

容器第一次跑起来时数据库是空的：没有账号、没填 Subsonic、没配 AI。
这里把「还差哪几步」聚合成一个接口，前端据此渲染向导，避免用户
去翻 .env 或猜环境变量名。
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Query
from sqlmodel import func, select

from app.api.deps import (
    AuthServiceDep,
    ConfigStoreDep,
    LLMSettingsServiceDep,
    SessionDep,
    SubsonicServiceDep,
    SubsonicSettingsServiceDep,
)
from app.database.models import Song
from app.schemas.auth import SetupStatusOut

router = APIRouter(prefix="/setup", tags=["setup"])


@router.get("/status", response_model=SetupStatusOut, summary="启动引导进度")
async def read_status(
    session: SessionDep,
    auth_service: AuthServiceDep,
    store: ConfigStoreDep,
    subsonic_settings: SubsonicSettingsServiceDep,
    subsonic_service: SubsonicServiceDep,
    llm_settings: LLMSettingsServiceDep,
    probe: bool = Query(
        default=False, description="是否真的连一次 Subsonic 服务器（慢，按需开启）"
    ),
) -> SetupStatusOut:
    needs_bootstrap = auth_service.needs_bootstrap(session)

    subsonic_view = subsonic_settings.to_view()
    connected: bool | None = None
    if probe and subsonic_view.configured:
        status = await subsonic_service.check(subsonic_settings.resolve())
        connected = status.connected

    llm_view = llm_settings.to_view()
    # mock provider 不需要 key 也算配好；真实 provider 必须有 key
    llm_configured = llm_view.provider == "mock" or llm_view.has_api_key

    song_count = int(session.exec(select(func.count()).select_from(Song)).one())

    return SetupStatusOut(
        needs_bootstrap=needs_bootstrap,
        account_ready=not needs_bootstrap,
        subsonic_configured=subsonic_view.configured,
        subsonic_connected=connected,
        llm_configured=llm_configured,
        llm_provider=llm_view.provider,
        library_synced=song_count > 0,
        song_count=song_count,
        completed=store.is_onboarding_completed(),
    )


@router.post("/complete", response_model=SetupStatusOut, summary="标记引导已完成")
async def complete(
    session: SessionDep,
    auth_service: AuthServiceDep,
    store: ConfigStoreDep,
    subsonic_settings: SubsonicSettingsServiceDep,
    subsonic_service: SubsonicServiceDep,
    llm_settings: LLMSettingsServiceDep,
) -> SetupStatusOut:
    store.set_onboarding_completed(datetime.now(timezone.utc).isoformat())
    return await read_status(
        session=session,
        auth_service=auth_service,
        store=store,
        subsonic_settings=subsonic_settings,
        subsonic_service=subsonic_service,
        llm_settings=llm_settings,
        probe=False,
    )

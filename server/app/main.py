"""应用入口（工厂模式，方便测试里造隔离实例）。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.deps import _config_store_singleton
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging, get_logger
from app.database.engine import init_db
from app.services.llm_settings_service import LLMSettingsService
from app.services.playlist_service import PlaylistService
from app.services.recommendation_service import RecommendationService
from app.services.scheduler_service import SchedulerService
from app.services.settings_service import SubsonicSettingsService

logger = get_logger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    init_db()

    # 构造调度器（复用与请求相同的服务单例），在应用生命周期内自动刷新每日推荐
    store = _config_store_singleton()
    subsonic_settings = SubsonicSettingsService(settings, store)
    llm_settings = LLMSettingsService(settings, store)
    rec_service = RecommendationService(llm_settings, subsonic_settings)
    playlist_service = PlaylistService(subsonic_settings)
    scheduler = SchedulerService(settings.scheduler, rec_service, playlist_service)
    app.state.scheduler = scheduler
    scheduler.start()

    logger.info("%s v%s 启动，API 前缀 %s", settings.app_name, __version__, settings.api_prefix)
    yield
    scheduler.shutdown()
    logger.info("服务已停止")


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_payload())

    @app.exception_handler(Exception)
    async def _unhandled_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("未捕获异常: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"code": "internal_error", "message": "服务内部错误", "detail": None},
        )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.server.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        debug=settings.debug,
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=_lifespan,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.server.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()

"""应用入口（工厂模式，方便测试里造隔离实例）。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

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
    _mount_web(app, settings)
    return app


def _mount_web(app: FastAPI, settings: Settings) -> None:
    """托管前端构建产物（web/dist）。

    仅当 ``SERVER__WEB_DIST`` 指向真实存在的目录时启用；
    非 API 路由全部回退到 index.html（SPA history 路由）。
    """

    if not settings.server.web_dist:
        return
    dist = Path(settings.server.web_dist).resolve()
    index = dist / "index.html"
    if not index.is_file():
        logger.warning("SERVER__WEB_DIST=%s 下未找到 index.html，跳过静态托管", dist)
        return

    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    api_prefix = settings.api_prefix

    @app.get("/{full_path:path}", include_in_schema=False)
    async def _spa(full_path: str) -> FileResponse:  # pragma: no cover - 容器部署路径
        if full_path.startswith(api_prefix.lstrip("/")):
            return JSONResponse(  # type: ignore[return-value]
                status_code=404,
                content={"code": "not_found", "message": "接口不存在", "detail": None},
            )
        candidate = (dist / full_path).resolve()
        # 防目录穿越 + 仅回真实文件，其余回 index.html
        if full_path and candidate.is_file() and str(candidate).startswith(str(dist)):
            return FileResponse(candidate)
        return FileResponse(index)

    logger.info("已托管前端静态文件：%s", dist)


app = create_app()

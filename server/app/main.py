"""应用入口（工厂模式，方便测试里造隔离实例）。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from app import __version__
from app.api.deps import _config_store_singleton
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging, get_logger
from app.database.engine import _engine, init_db
from app.services.auth_service import AuthService
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


# 无需登录即可访问的 API 路径（相对 api_prefix）。
# 只放行「决定去哪个页面」和「怎么登录」所必需的最小集合。
_PUBLIC_API_PATHS = frozenset(
    {
        "/health",
        "/auth/session",
        "/auth/login",
        "/auth/logout",
        "/auth/bootstrap",
    }
)


def _register_auth_middleware(app: FastAPI, settings: Settings) -> None:
    """Cookie 会话鉴权。

    只拦 API 前缀下的请求：前端静态资源必须放行，否则登录页自己都加载不出来；
    未登录时由 SPA 自行跳转到 /login。
    """

    if not settings.auth.enabled:
        logger.warning("AUTH__ENABLED=false，已关闭登录校验（仅建议在受信内网调试时使用）")
        return

    api_prefix = settings.api_prefix.rstrip("/")
    public_paths = {f"{api_prefix}{path}" for path in _PUBLIC_API_PATHS}
    auth_service = AuthService(settings.auth.session_ttl_hours)
    cookie_name = settings.auth.cookie_name

    @app.middleware("http")
    async def _auth_guard(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path
        if (
            request.method == "OPTIONS"  # CORS 预检
            or not path.startswith(api_prefix)  # 静态资源 / SPA / docs
            or path in public_paths
        ):
            return await call_next(request)

        token = request.cookies.get(cookie_name)
        with Session(_engine) as session:
            user = auth_service.resolve(session, token)
            # 一个账号都没有时不该把人挡在门外，否则引导流程无从开始
            if user is None and auth_service.needs_bootstrap(session):
                return JSONResponse(
                    status_code=401,
                    content={
                        "code": "needs_bootstrap",
                        "message": "系统尚未初始化，请先完成启动引导",
                        "detail": None,
                    },
                )
        if user is None:
            return JSONResponse(
                status_code=401,
                content={
                    "code": "unauthorized",
                    "message": "未登录或登录已过期",
                    "detail": None,
                },
            )
        return await call_next(request)


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

    # 注意：中间件按「后注册先执行」的顺序包裹，鉴权放在 CORS 之后注册，
    # 这样 401 响应同样会带上 CORS 头，浏览器才读得到错误码。
    _register_auth_middleware(app, settings)
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

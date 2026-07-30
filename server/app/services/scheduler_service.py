"""定时调度服务（APScheduler）。

在应用生命周期内自动刷新「每日推荐」歌单：默认每天 09:00（Asia/Shanghai）
运行一次，同日再跑会刷新而非新建。调度器跑在 uvicorn 的同一事件循环里，
任务内部自己开一个独立 DB 会话，异常不会拖垮调度器。
"""

from __future__ import annotations

import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session

from app.core.config import SchedulerSettings
from app.core.logging import get_logger
from app.database.engine import _engine
from app.services.daily_mix_service import DailyMixService
from app.services.playlist_service import PlaylistService
from app.services.recommendation_service import RecommendationService

logger = get_logger(__name__)

_TZ = "Asia/Shanghai"


class SchedulerService:
    def __init__(
        self,
        settings: SchedulerSettings,
        recommendation_service: RecommendationService,
        playlist_service: PlaylistService,
    ) -> None:
        self._settings = settings
        self._rec = recommendation_service
        self._playlist = playlist_service
        self._scheduler = AsyncIOScheduler(timezone=_TZ)
        self._last_run: dict | None = None

    # ----------------------------------------------------------- 生命周期
    def start(self) -> None:
        if not self._settings.enabled:
            logger.info("定时任务已禁用（scheduler.enabled=false），不启动调度器")
            return
        trigger = CronTrigger(
            hour=self._settings.daily_mix_hour,
            minute=self._settings.daily_mix_minute,
            timezone=_TZ,
        )
        self._scheduler.add_job(
            self._run_daily_mix,
            trigger,
            id="daily_mix",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self._scheduler.start()
        logger.info(
            "调度器已启动：每日 %02d:%02d 自动生成/刷新「每日推荐」",
            self._settings.daily_mix_hour,
            self._settings.daily_mix_minute,
        )

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
        logger.info("调度器已停止")

    # ----------------------------------------------------------- 手动触发
    def trigger_now(self) -> bool:
        """立即跑一次每日推荐（与 enabled 无关）。返回是否成功派发。"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.warning("无运行中的事件循环，无法手动触发每日推荐")
            return False
        loop.create_task(self._run_daily_mix())
        logger.info("已提交手动触发：每日推荐")
        return True

    # ----------------------------------------------------------- 状态
    def status(self) -> dict:
        next_run = None
        job = self._scheduler.get_job("daily_mix")
        if job is not None and job.next_run_time is not None:
            next_run = job.next_run_time.isoformat()
        return {
            "enabled": self._settings.enabled,
            "running": self._scheduler.running,
            "daily_mix_hour": self._settings.daily_mix_hour,
            "daily_mix_minute": self._settings.daily_mix_minute,
            "next_run": next_run,
            "last_run": self._last_run,
        }

    # ----------------------------------------------------------- 任务体
    async def _run_daily_mix(self) -> None:
        logger.info("⏰ 定时任务触发：生成每日推荐")
        with Session(_engine) as session:
            svc = DailyMixService(self._rec, self._playlist)
            try:
                result = await svc.generate(session)
            except Exception as exc:  # 单任务失败不应拖垮调度器
                logger.exception("每日推荐定时任务失败: %s", exc)
                self._last_run = {
                    "ok": False,
                    "at": datetime.now().isoformat(timespec="seconds"),
                    "error": str(exc),
                }
                return
        self._last_run = {
            "ok": True,
            "at": datetime.now().isoformat(timespec="seconds"),
            "theme": result.theme,
            "songs": len(result.recommendation.songs),
            "playlist": result.playlist.name if result.playlist else None,
            "action": "refresh" if result.refreshed else ("create" if result.created else "none"),
        }
        logger.info(
            "每日推荐定时任务完成：%s（%d 首，%s）",
            self._last_run["playlist"],
            self._last_run["songs"],
            self._last_run["action"],
        )

"""音乐库同步接口。"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Query, status
from sqlmodel import Session, select

from app.api.deps import BrowseServiceDep, LibrarySyncServiceDep
from app.database import models
from app.database.engine import _engine
from app.schemas.library import SyncStateOut

router = APIRouter(prefix="/library", tags=["library"])

# 进行中的状态——出现这些状态时不再叠加新的同步任务
_ACTIVE_STATUSES = ("queued", "running")


@router.post(
    "/sync",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SyncStateOut,
    summary="触发一次库同步（异步后台执行）",
)
async def trigger_sync(
    background: BackgroundTasks,
    sync_service: LibrarySyncServiceDep,
    mode: str = Query("full", pattern="^(full|incremental)$"),
) -> SyncStateOut:
    # 防重入：已有 queued/running 的任务则直接返回，避免叠加同步把库清空两次
    with Session(_engine) as probe:
        latest = probe.exec(
            select(models.SyncState).order_by(models.SyncState.started_at.desc()).limit(1)
        ).first()
        if latest is not None and latest.status in _ACTIVE_STATUSES:
            return SyncStateOut.model_validate(latest)

    # 预建 queued 记录并拿到 id，立即返回 202；真正的同步在后台任务里跑
    with Session(_engine) as s:
        queued = models.SyncState(scope="library", status="queued")
        s.add(queued)
        s.commit()
        s.refresh(queued)
        queued_out = SyncStateOut.model_validate(queued)
        queued_id = queued.id

    async def _run() -> None:
        # 后台任务用独立的 DB 会话，避免复用请求会话（请求结束后会关闭）
        with Session(_engine) as s:
            rec = s.get(models.SyncState, queued_id)
            if rec is None:
                return
            await sync_service.sync(s, mode=mode, state=rec)

    background.add_task(_run)
    return queued_out


@router.get("/sync/status", summary="最近一次同步状态")
def sync_status(browse: BrowseServiceDep) -> SyncStateOut | dict:
    state = browse.latest_sync_state()
    if state is None:
        return {"status": "never"}
    return SyncStateOut.model_validate(state)

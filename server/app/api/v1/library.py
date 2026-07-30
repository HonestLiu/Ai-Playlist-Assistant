"""音乐库同步接口。"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import BrowseServiceDep, LibrarySyncServiceDep, SessionDep
from app.schemas.library import SyncStateOut

router = APIRouter(prefix="/library", tags=["library"])


@router.post("/sync", response_model=SyncStateOut, summary="触发一次库同步")
async def trigger_sync(
    sync_service: LibrarySyncServiceDep,
    session: SessionDep,
    mode: str = Query("full", pattern="^(full|incremental)$"),
) -> SyncStateOut:
    state = await sync_service.sync(session, mode=mode)
    return SyncStateOut.model_validate(state)


@router.get("/sync/status", summary="最近一次同步状态")
def sync_status(browse: BrowseServiceDep) -> SyncStateOut | dict:
    state = browse.latest_sync_state()
    if state is None:
        return {"status": "never"}
    return SyncStateOut.model_validate(state)

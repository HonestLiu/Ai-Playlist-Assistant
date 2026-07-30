"""v1 路由汇总。新增模块只需要在这里挂一行。"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    ai,
    albums,
    artists,
    auth,
    library,
    play_history,
    playlists,
    settings,
    setup,
    songs,
    stream,
    subsonic,
    system,
)

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(setup.router)
api_router.include_router(settings.router)
api_router.include_router(subsonic.router)
api_router.include_router(stream.router)
api_router.include_router(play_history.router)
api_router.include_router(library.router)
api_router.include_router(artists.router)
api_router.include_router(albums.router)
api_router.include_router(songs.router)
api_router.include_router(ai.router)
api_router.include_router(playlists.router)

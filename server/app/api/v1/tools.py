"""音乐库管理工具接口：重复歌曲检测 / 删除 / 歌单去重 / 信息缺失扫描。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import (
    RequireUserDep,
    SessionDep,
    SubsonicSettingsServiceDep,
)
from app.core.errors import AppError
from app.schemas.tools import (
    DeleteDuplicatesRequest,
    DeleteResultOut,
    DuplicateReportOut,
    MetadataGapReportOut,
    PlaylistCleanRequest,
    PlaylistCleanResultOut,
    PlaylistDuplicateReportOut,
)
from app.services.library_tools_service import LibraryToolsService

router = APIRouter(prefix="/tools", tags=["tools"])


def _service(sub_setting: SubsonicSettingsServiceDep) -> LibraryToolsService:
    return LibraryToolsService(sub_setting)


@router.get(
    "/duplicates",
    response_model=DuplicateReportOut,
    summary="扫描本地歌曲，找出疑似重复",
)
def scan_duplicates(
    session: SessionDep,
    sub_setting: SubsonicSettingsServiceDep,
    _: RequireUserDep,
) -> DuplicateReportOut:
    return _service(sub_setting).find_duplicates(session)


@router.post(
    "/duplicates/delete",
    response_model=DeleteResultOut,
    summary="从 Subsonic 删除指定重复歌曲（需管理员权限，不可逆）",
)
async def delete_duplicates(
    session: SessionDep,
    sub_setting: SubsonicSettingsServiceDep,
    _: RequireUserDep,
    payload: DeleteDuplicatesRequest,
) -> DeleteResultOut:
    try:
        return await _service(sub_setting).delete_songs(session, payload.song_ids)
    except AppError:
        raise
    except Exception as exc:  # 避免内部异常泄露为 500 无信息
        raise AppError(message=f"删除失败：{exc}", code="delete_failed")


@router.get(
    "/playlists/duplicates",
    response_model=PlaylistDuplicateReportOut,
    summary="扫描本地歌单，找出歌单内重复歌曲",
)
def scan_playlist_duplicates(
    session: SessionDep,
    sub_setting: SubsonicSettingsServiceDep,
    _: RequireUserDep,
) -> PlaylistDuplicateReportOut:
    return _service(sub_setting).find_playlist_duplicates(session)


@router.post(
    "/playlists/duplicates/clean",
    response_model=PlaylistCleanResultOut,
    summary="对指定歌单做去重（保留每首歌首次出现）",
)
async def clean_playlist_duplicates(
    session: SessionDep,
    sub_setting: SubsonicSettingsServiceDep,
    _: RequireUserDep,
    payload: PlaylistCleanRequest,
) -> PlaylistCleanResultOut:
    try:
        return await _service(sub_setting).clean_playlist(session, payload.subsonic_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AppError:
        raise
    except Exception as exc:
        raise AppError(message=f"歌单去重失败：{exc}", code="playlist_clean_failed")


@router.get(
    "/metadata-gaps",
    response_model=MetadataGapReportOut,
    summary="扫描信息缺失（缺封面 / 年份 / 流派 / 专辑）的歌曲",
)
def scan_metadata_gaps(
    session: SessionDep,
    sub_setting: SubsonicSettingsServiceDep,
    _: RequireUserDep,
) -> MetadataGapReportOut:
    return _service(sub_setting).find_metadata_gaps(session)

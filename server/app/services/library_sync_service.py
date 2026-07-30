"""音乐库同步服务。

职责：把 Subsonic 服务器上的库「搬」进本地 SQLite，供浏览与未来的 AI 推荐使用。

同步策略（Phase 2）：
- **全量同步（full）**：先清空三张表，再整体写入。逻辑简单、天然一致，适合当前
  库规模（数十~数千首）。
- **增量同步（incremental）**：本 Phase 先留接口但不启用——zmusicv2 不返回
  ``lastUpdated``，``modifiedSince`` 不可靠。未来遇到支持增量的服务器再在此分支落地。

可靠性约束：先**完整拉取**服务器数据，确认无误后再在一个事务里清+写。这样即使
中途网络失败，本地库也不会被清成空。
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from sqlmodel import Session, delete

from app.core.logging import get_logger
from app.database import models
from app.services.settings_service import SubsonicSettingsService
from app.subsonic.client import SubsonicClient
from app.subsonic.exceptions import SubsonicError, SubsonicNotConfiguredError

logger = get_logger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class LibrarySyncService:
    def __init__(self, settings_service: SubsonicSettingsService) -> None:
        self._settings_service = settings_service

    async def sync(self, session: Session, *, mode: str = "full") -> models.SyncState:
        """执行一次同步，返回同步任务记录。

        ``mode`` 为 ``full`` 时清空后整体写入；为 ``incremental`` 时当前退化为全量
        （服务器不支持增量），仅记录日志，不抛错。
        """

        config = self._settings_service.resolve()
        if not config.is_complete:
            raise SubsonicNotConfiguredError()

        if mode not in ("full", "incremental"):
            raise ValueError(f"未知同步模式: {mode}")

        # 先落一条 running 记录，前端轮询能看到「进行中」
        state = models.SyncState(scope="library", status="running")
        session.add(state)
        session.commit()
        session.refresh(state)

        started = time.perf_counter()
        try:
            async with SubsonicClient(config) as client:
                folders = await client.get_music_folders()
                folder_id = folders[0].id if folders else None

                # 第一阶段：只从服务器读，不动库
                # 用 dict 按 ID 去重——合辑/群星专辑会同时挂在多个艺术家下，
                # 不然后面插库会撞主键 UNIQUE constraint。
                artist_rows: list[models.Artist] = []
                album_map: dict[str, models.Album] = {}
                song_map: dict[str, models.Song] = {}

                artists = await client.get_artists(music_folder_id=folder_id)
                for art in artists:
                    artist_rows.append(
                        models.Artist(
                            id=art.id,
                            name=art.name,
                            album_count=art.album_count,
                            song_count=art.song_count,
                            cover_art=art.cover_art,
                            music_folder_id=folder_id,
                            synced_at=_now(),
                        )
                    )
                    _, albums = await client.get_artist(art.id)
                    for alb in albums:
                        if alb.id in album_map:
                            continue
                        album_map[alb.id] = models.Album(
                            id=alb.id,
                            name=alb.name,
                            artist_id=alb.artist_id or art.id,
                            artist_name=alb.artist_name or art.name,
                            cover_art=alb.cover_art,
                            song_count=alb.song_count,
                            duration=alb.duration,
                            year=alb.year,
                            genre=alb.genre,
                            music_folder_id=folder_id,
                            synced_at=_now(),
                        )
                        _, songs = await client.get_album(alb.id)
                        for song in songs:
                            if song.id in song_map:
                                continue
                            song_map[song.id] = models.Song(
                                id=song.id,
                                title=song.title,
                                album_id=song.album_id or alb.id,
                                album_name=song.album_name or alb.name,
                                artist_id=song.artist_id or art.id,
                                artist_name=song.artist_name or art.name,
                                track=song.track,
                                year=song.year,
                                genre=song.genre,
                                duration=song.duration,
                                bit_rate=song.bit_rate,
                                size=song.size,
                                content_type=song.content_type,
                                suffix=song.suffix,
                                path=song.path,
                                cover_art=song.cover_art,
                                music_folder_id=folder_id,
                                synced_at=_now(),
                            )

            # 第二阶段：一次性清+写
            if mode == "full":
                session.exec(delete(models.Song))
                session.exec(delete(models.Album))
                session.exec(delete(models.Artist))
            session.add_all(artist_rows)
            session.add_all(list(album_map.values()))
            session.add_all(list(song_map.values()))
            session.commit()

            state.status = "success"
            state.artists_synced = len(artist_rows)
            state.albums_synced = len(album_map)
            state.songs_synced = len(song_map)
            state.finished_at = _now()
            session.commit()
            session.refresh(state)

            logger.info(
                "库同步完成(%s)：%d 艺术家 / %d 专辑 / %d 歌曲，耗时 %.1fs",
                mode,
                len(artist_rows),
                len(album_map),
                len(song_map),
                time.perf_counter() - started,
            )
            return state

        except SubsonicError as exc:
            logger.warning("库同步失败：%s - %s", exc.code, exc.message)
            state.status = "failed"
            state.error = f"{exc.code}: {exc.message}"
            state.finished_at = _now()
            session.commit()
            session.refresh(state)
            return state
        except Exception as exc:  # noqa: BLE001 - 同步失败不应升级为 500 风暴
            logger.exception("库同步异常")
            state.status = "failed"
            state.error = str(exc)[:500]
            state.finished_at = _now()
            session.commit()
            session.refresh(state)
            return state

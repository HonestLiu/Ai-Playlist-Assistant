"""音乐库管理工具服务：重复歌曲检测 / 删除 / 歌单去重 / 信息缺失扫描。

全部基于**本地 SQLite** 做只读分析，只在用户明确触发「删除」时才去碰 Subsonic。
这样既能离线跑，也避免把分析压力转嫁给 Subsonic 服务器。
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, func, select

from app.core.logging import get_logger
from app.database import models
from app.schemas.tools import (
    DeleteFailure,
    DeleteResultOut,
    DuplicateGroupOut,
    DuplicateReportOut,
    DuplicateSongOut,
    MetadataGapOut,
    MetadataGapReportOut,
    PlaylistCleanResultOut,
    PlaylistDuplicateEntry,
    PlaylistDuplicateOut,
    PlaylistDuplicateReportOut,
)
from app.services.settings_service import SubsonicSettingsService
from app.subsonic.client import SubsonicClient
from app.subsonic.exceptions import SubsonicError

logger = get_logger(__name__)

# 时长容忍窗口（秒）：同一专辑内时长差 ≤ 该值视为同一音轨
_DURATION_TOLERANCE = 3

# 用于「归一化」的非法字符：保留字母、数字与中日韩文字
_NON_ALNUM_RE = re.compile(r"[^a-z0-9一-鿿]")


def _norm(text: Optional[str]) -> str:
    """把标题/艺术家/专辑名归一化，用于忽略大小写、空格与标点的比较。"""

    if not text:
        return ""
    return _NON_ALNUM_RE.sub("", text.lower()).strip()


def _duration_bucket(duration: Optional[int]) -> Optional[int]:
    """把时长离散到 ``_DURATION_TOLERANCE`` 秒的桶里，None 不参比。"""

    if duration is None:
        return None
    return int(round(duration / _DURATION_TOLERANCE)) * _DURATION_TOLERANCE


class LibraryToolsService:
    def __init__(self, subsonic_settings_service: SubsonicSettingsService) -> None:
        self._sub = subsonic_settings_service

    # ------------------------------------------------------------------ 重复歌曲
    def find_duplicates(self, session: Session) -> DuplicateReportOut:
        """扫描本地歌曲，找出「同一音轨在库中多次出现」的疑似重复。

        判定逻辑（高置信度，尽量少误报）：

        1. 完全相同的 ``path``（文件级重复）无论在哪个专辑/标题下都强制归并；
        2. 再按归一化的「标题 + 艺术家」分候选组，组内按「归一化专辑 + 时长桶」
           （时长差 ≤ 3s）聚类；
        3. 任一簇内 ≥ 2 首即为重复，保留音质/体积最佳的一首，其余标记为可清理。

        用全局并查集把上述两类信号合并，复杂度控制在 O(n + Σ组内两两比较)，
        不会退化为整库 O(n²)。
        """

        songs = list(session.exec(select(models.Song)).all())
        total = len(songs)

        groups: list[DuplicateGroupOut] = []
        removable = 0

        n = len(songs)
        if n < 2:
            return DuplicateReportOut(
                total_songs=total,
                groups=groups,
                removable_count=0,
                scanned_at=datetime.now(timezone.utc),
            )

        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        # 信号一：完全相同的文件路径（跨候选组也归并）
        by_path: dict[str, list[int]] = defaultdict(list)
        for idx, song in enumerate(songs):
            if song.path:
                by_path[song.path].append(idx)
        for ids in by_path.values():
            for other in ids[1:]:
                union(ids[0], other)

        # 信号二：同一「标题 + 艺术家」候选组内，同专辑且时长桶一致
        by_candidate: dict[tuple[str, str], list[int]] = defaultdict(list)
        for idx, song in enumerate(songs):
            key = (_norm(song.title), _norm(song.artist_name))
            by_candidate[key].append(idx)

        for members in by_candidate.values():
            if len(members) < 2:
                continue
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    a, b = songs[members[i]], songs[members[j]]
                    same_album = (
                        _norm(a.album_name)
                        and _norm(a.album_name) == _norm(b.album_name)
                    )
                    ba, bb = _duration_bucket(a.duration), _duration_bucket(b.duration)
                    same_track = bool(
                        same_album and ba is not None and bb is not None and ba == bb
                    )
                    if same_track:
                        union(members[i], members[j])

        clusters: dict[int, list[models.Song]] = defaultdict(list)
        for idx, song in enumerate(songs):
            clusters[find(idx)].append(song)

        for cluster in clusters.values():
            if len(cluster) < 2:
                continue
            kept, dups = self._pick_keep(cluster)
            reason = self._reason_for(cluster)
            groups.append(
                DuplicateGroupOut(
                    key=f"{_norm(cluster[0].title)}|{_norm(cluster[0].artist_name)}",
                    title=cluster[0].title or "(未知标题)",
                    artist=cluster[0].artist_name or "(未知艺术家)",
                    kept=DuplicateSongOut.model_validate(kept),
                    duplicates=[DuplicateSongOut.model_validate(d) for d in dups],
                    reason=reason,
                )
            )
            removable += len(dups)

        groups.sort(key=lambda g: (g.artist, g.title))
        return DuplicateReportOut(
            total_songs=total,
            groups=groups,
            removable_count=removable,
            scanned_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _pick_keep(cluster: list[models.Song]) -> tuple[models.Song, list[models.Song]]:
        """从一簇中选出「最佳」保留，其余返回为可清理副本。"""

        best = sorted(
            cluster,
            key=lambda s: (
                s.bit_rate or 0,
                s.size or 0,
                s.duration or 0,
                s.id,
            ),
            reverse=True,
        )[0]
        duplicates = [s for s in cluster if s.id != best.id]
        return best, duplicates

    @staticmethod
    def _reason_for(cluster: list[models.Song]) -> str:
        album = cluster[0].album_name
        if any(a.path and a.path == b.path for i, a in enumerate(cluster) for b in cluster[i + 1 :]):
            return "检测到完全相同的文件路径"
        if album:
            return f"同一专辑《{album}》内存在时长一致的重复音轨"
        return "标题与艺术家一致，且时长相同，疑似重复"

    # ------------------------------------------------------------------ 删除
    async def delete_songs(
        self, session: Session, song_ids: list[str]
    ) -> DeleteResultOut:
        """从 Subsonic 服务器删除给定歌曲，并同步清理本地记录。

        逐首删除，失败的单独记录，不中断其余；只有真正删成功的才会从本地库移除，
        避免出现「服务器没了、本地还在」的不一致。
        """

        config = self._sub.resolve()
        failures: list[DeleteFailure] = []
        deleted_ids: list[str] = []

        if not config.is_complete:
            return DeleteResultOut(
                requested=len(song_ids),
                deleted=0,
                failed=[DeleteFailure(id=sid, error="Subsonic 未配置，无法删除") for sid in song_ids],
            )

        async with SubsonicClient(config) as client:
            for song_id in song_ids:
                try:
                    await client.delete_song(song_id)
                    deleted_ids.append(song_id)
                except SubsonicError as exc:
                    failures.append(DeleteFailure(id=song_id, error=exc.message))
                except Exception as exc:  # 兜底，避免单首失败拖垮整体
                    failures.append(DeleteFailure(id=song_id, error=str(exc)))

        if deleted_ids:
            for song in session.exec(
                select(models.Song).where(models.Song.id.in_(deleted_ids))
            ).all():
                session.delete(song)
            # 顺带从本地歌单记录里摘除已删除的歌曲
            for playlist in session.exec(select(models.Playlist)).all():
                remaining = [sid for sid in playlist.song_ids if sid not in set(deleted_ids)]
                if len(remaining) != len(playlist.song_ids):
                    playlist.song_ids = remaining
                    playlist.song_count = len(remaining)
                    session.add(playlist)
            session.commit()

        logger.info(
            "重复歌曲删除：请求 %d，成功 %d，失败 %d",
            len(song_ids),
            len(deleted_ids),
            len(failures),
        )
        return DeleteResultOut(
            requested=len(song_ids),
            deleted=len(deleted_ids),
            failed=failures,
        )

    # ------------------------------------------------------------------ 歌单去重
    def find_playlist_duplicates(self, session: Session) -> PlaylistDuplicateReportOut:
        """扫描本地记录的歌单，找出歌单内重复出现的歌曲。

        重复定义：同一 ``song_id`` 出现多次，或不同 ``song_id`` 但「标题 + 艺术家」一致
        （如同一首歌被加进不同专辑两次）。清理时保留首次出现。
        """

        playlists = list(session.exec(select(models.Playlist)).all())
        song_lookup = {
            s.id: s
            for s in session.exec(
                select(models.Song).where(
                    models.Song.id.in_(
                        {sid for p in playlists for sid in p.song_ids}
                    )
                )
            ).all()
        }

        out_playlists: list[PlaylistDuplicateOut] = []
        with_dupes = 0
        total_removable = 0

        for playlist in playlists:
            entries = [
                (sid, (song_lookup.get(sid).title if song_lookup.get(sid) else None),
                 (song_lookup.get(sid).artist_name if song_lookup.get(sid) else None))
                for sid in playlist.song_ids
            ]
            key_counter = Counter((t, a) for _, t, a in entries)
            dup_entries: list[PlaylistDuplicateEntry] = []
            for (title, artist), count in key_counter.items():
                if count > 1:
                    sid = next((s for s, t, a in entries if t == title and a == artist), "")
                    dup_entries.append(
                        PlaylistDuplicateEntry(
                            song_id=sid,
                            title=title or "(未知标题)",
                            artist=artist or "(未知艺术家)",
                            occurrences=count,
                        )
                    )
            unique_count = len({(t, a) for _, t, a in entries})
            if dup_entries:
                with_dupes += 1
                total_removable += len(playlist.song_ids) - unique_count
            out_playlists.append(
                PlaylistDuplicateOut(
                    playlist_id=str(playlist.id),
                    subsonic_id=playlist.subsonic_id,
                    name=playlist.name,
                    source=playlist.source,
                    song_count=playlist.song_count,
                    unique_count=unique_count,
                    duplicates=dup_entries,
                )
            )

        out_playlists.sort(key=lambda p: p.name)
        return PlaylistDuplicateReportOut(
            playlists=out_playlists,
            playlists_with_duplicates=with_dupes,
            total_removable=total_removable,
        )

    async def clean_playlist(self, session: Session, subsonic_id: str) -> PlaylistCleanResultOut:
        """对一个歌单做去重：保留每首歌（按 标题+艺术家 / song_id）的首次出现。"""

        playlist = session.exec(
            select(models.Playlist).where(models.Playlist.subsonic_id == subsonic_id)
        ).first()
        if playlist is None:
            raise ValueError(f"找不到歌单 {subsonic_id}")

        seen_ids: set[str] = set()
        seen_keys: set[tuple[Optional[str], Optional[str]]] = set()
        deduped: list[str] = []
        for sid in playlist.song_ids:
            song = session.get(models.Song, sid)
            title = song.title if song else None
            artist = song.artist_name if song else None
            key = (_norm(title), _norm(artist))
            if sid in seen_ids or key in seen_keys:
                continue
            seen_ids.add(sid)
            seen_keys.add(key)
            deduped.append(sid)

        removed = len(playlist.song_ids) - len(deduped)
        config = self._sub.resolve()
        async with SubsonicClient(config) as client:
            await client.update_playlist(playlist.subsonic_id, song_ids=list(deduped))

        duration = (
            session.exec(
                select(func.coalesce(func.sum(models.Song.duration), 0)).where(
                    models.Song.id.in_(deduped)
                )
            ).first()
            or 0
        )
        playlist.song_ids = list(deduped)
        playlist.song_count = len(deduped)
        playlist.duration = int(duration or 0)
        session.add(playlist)
        session.commit()
        session.refresh(playlist)

        logger.info("歌单去重 %s：移除 %d 首，剩余 %d 首", subsonic_id, removed, len(deduped))
        return PlaylistCleanResultOut(
            playlist_id=str(playlist.id),
            name=playlist.name,
            removed=removed,
            new_count=len(deduped),
        )

    # ------------------------------------------------------------------ 信息缺失
    def find_metadata_gaps(self, session: Session) -> MetadataGapReportOut:
        """统计缺失封面 / 年份 / 流派 / 专辑归属的歌曲，并附样例。"""

        total = session.exec(select(func.count()).select_from(models.Song)).one()

        def _count(where) -> int:
            return session.exec(select(func.count()).select_from(models.Song).where(where)).one()

        def _samples(where, limit: int = 20) -> list[DuplicateSongOut]:
            rows = session.exec(select(models.Song).where(where).limit(limit)).all()
            return [DuplicateSongOut.model_validate(r) for r in rows]

        gaps: list[MetadataGapOut] = []
        no_cover = (models.Song.cover_art.is_(None)) | (models.Song.cover_art == "")
        no_year = models.Song.year.is_(None)
        no_genre = (models.Song.genre.is_(None)) | (models.Song.genre == "")
        no_album = (models.Song.album_name.is_(None)) | (models.Song.album_name == "")

        gaps.append(
            MetadataGapOut(
                category="missing_cover",
                label="缺少封面",
                count=_count(no_cover),
                samples=_samples(no_cover),
            )
        )
        gaps.append(
            MetadataGapOut(
                category="missing_year",
                label="缺少年份",
                count=_count(no_year),
                samples=_samples(no_year),
            )
        )
        gaps.append(
            MetadataGapOut(
                category="missing_genre",
                label="缺少流派",
                count=_count(no_genre),
                samples=_samples(no_genre),
            )
        )
        gaps.append(
            MetadataGapOut(
                category="missing_album",
                label="缺少专辑归属",
                count=_count(no_album),
                samples=_samples(no_album),
            )
        )

        return MetadataGapReportOut(
            total_songs=total,
            gaps=gaps,
            scanned_at=datetime.now(timezone.utc),
        )

"""Subsonic API 客户端。

这是整个服务端**唯一**允许发起 Subsonic HTTP 请求的地方。
业务代码只依赖这里暴露的方法，不感知 salt/token、``subsonic-response``
包裹结构、错误码等协议细节。

Phase 1 只实现连通性相关的接口，后续 Phase 在这里按分组继续扩展
（音乐库、专辑、艺术家、歌曲、歌单……）。
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone
from types import TracebackType
from typing import Any, Self

import httpx

from app.core.logging import get_logger
from app.models.library import (
    MusicFolder,
    SubsonicAlbum,
    SubsonicArtist,
    SubsonicSong,
)
from app.models.subsonic import (
    SubsonicConnectionConfig,
    SubsonicPlaylist,
    SubsonicServerInfo,
)
from app.subsonic.exceptions import (
    SubsonicNotConfiguredError,
    SubsonicResponseError,
    SubsonicTimeoutError,
    SubsonicUnavailableError,
    map_subsonic_error,
)

logger = get_logger(__name__)

_RESPONSE_KEY = "subsonic-response"


class SubsonicClient:
    """异步 Subsonic 客户端。

    用法::

        async with SubsonicClient(config) as client:
            info = await client.ping()
    """

    def __init__(
        self,
        config: SubsonicConnectionConfig,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        if not config.is_complete:
            raise SubsonicNotConfiguredError()
        self._config = config
        self._owns_client = http_client is None
        self._http = http_client or httpx.AsyncClient(
            timeout=config.timeout,
            verify=config.verify_ssl,
            follow_redirects=True,
        )

    # ------------------------------------------------------------------ 生命周期
    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._http.aclose()

    # ------------------------------------------------------------------ 认证
    def _auth_params(self) -> dict[str, str]:
        cfg = self._config
        params: dict[str, str] = {
            "u": cfg.username,
            "v": cfg.api_version,
            "c": cfg.client_name,
            "f": "json",
        }
        if cfg.legacy_auth:
            params["p"] = f"enc:{cfg.password.encode('utf-8').hex()}"
        else:
            salt = secrets.token_hex(8)
            token = hashlib.md5(f"{cfg.password}{salt}".encode("utf-8")).hexdigest()
            params["t"] = token
            params["s"] = salt
        return params

    # ------------------------------------------------------------------ 请求核心
    async def _request(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """发送请求并返回已解包、已校验的 ``subsonic-response`` 内容。

        注意：本环境的 httpx 拦截了 async POST，但 Subsonic 的 ``.view`` 端点
        本质是 GET，因此所有写操作（建/改/删歌单）也走 GET，用重复参数
        （如 ``songId`` 多次）表达列表。``params`` 的值允许是 ``list``，
        会被展开成多个同名键值对。
        """

        url = f"{self._config.rest_base_url}/{endpoint}"
        pairs: list[tuple[str, str]] = [
            (k, self._encode_param(v)) for k, v in self._auth_params().items()
        ]
        for key, value in (params or {}).items():
            if value is None:
                continue
            if isinstance(value, list):
                pairs.extend((key, self._encode_param(item)) for item in value)
            else:
                pairs.append((key, self._encode_param(value)))

        logger.debug("Subsonic 请求: %s", endpoint)
        try:
            response = await self._http.get(url, params=pairs)
        except httpx.TimeoutException as exc:
            raise SubsonicTimeoutError(detail=str(exc)) from exc
        except httpx.HTTPError as exc:
            raise SubsonicUnavailableError(detail=str(exc)) from exc

        if response.status_code >= 400:
            raise SubsonicUnavailableError(
                f"Subsonic 返回 HTTP {response.status_code}",
                detail=response.text[:200],
            )

        try:
            body = response.json()
        except ValueError as exc:
            raise SubsonicResponseError(
                "响应不是合法 JSON，请确认地址指向的是 Subsonic 服务器",
                detail=response.text[:200],
            ) from exc

        payload = body.get(_RESPONSE_KEY)
        if not isinstance(payload, dict):
            raise SubsonicResponseError(detail=str(body)[:200])

        if payload.get("status") != "ok":
            error = payload.get("error") or {}
            raise map_subsonic_error(error.get("code"), error.get("message"))

        return payload

    # ------------------------------------------------------------------ 公开接口
    async def ping(self) -> SubsonicServerInfo:
        """连通性 + 凭据校验。失败会抛出具体的 Subsonic* 异常。"""

        payload = await self._request("ping.view")
        return SubsonicServerInfo(
            version=payload.get("version"),
            server_type=payload.get("type"),
            server_version=payload.get("serverVersion"),
            open_subsonic=bool(payload.get("openSubsonic", False)),
        )

    # ------------------------------------------------------------------ 音乐库浏览
    async def get_music_folders(self) -> list[MusicFolder]:
        """返回音乐库根目录列表。"""

        payload = await self._request("getMusicFolders.view")
        folders = payload.get("musicFolders", {}).get("musicFolder", [])
        return [MusicFolder(id=int(f["id"]), name=f.get("name", "")) for f in folders]

    async def get_artists(self, music_folder_id: int | None = None) -> list[SubsonicArtist]:
        """返回全部艺术家（按字母分组展开）。

        这是同步的**权威源**——zmusicv2 的 ``getIndexes`` 返回 ``folder-`` 前缀 ID，
        无法用于 ``getArtist``，而 ``getArtists`` 的 ID 可用。
        """

        params = {"musicFolderId": music_folder_id} if music_folder_id is not None else {}
        payload = await self._request("getArtists.view", params)
        indices = payload.get("artists", {})
        index_list = indices.get("index", []) if isinstance(indices, dict) else (indices or [])
        artists: list[SubsonicArtist] = []
        for index in index_list:
            if not isinstance(index, dict):
                continue
            for raw in index.get("artist", []):
                if not isinstance(raw, dict) or not raw.get("id"):
                    continue
                artists.append(
                    SubsonicArtist(
                        id=raw["id"],
                        name=raw.get("name", ""),
                        album_count=raw.get("albumCount"),
                        song_count=raw.get("songCount"),
                        cover_art=raw.get("coverArt"),
                    )
                )
        return artists

    async def get_artist(self, artist_id: str) -> tuple[SubsonicArtist, list[SubsonicAlbum]]:
        """返回单个艺术家及其专辑列表。"""

        payload = await self._request("getArtist.view", {"id": artist_id})
        raw = payload.get("artist", {})
        if isinstance(raw, list):
            raw = raw[0] if raw else {}
        if not isinstance(raw, dict):
            raw = {}
        artist = SubsonicArtist(
            id=raw.get("id") or artist_id,
            name=raw.get("name", ""),
            album_count=raw.get("albumCount"),
            song_count=raw.get("songCount"),
            cover_art=raw.get("coverArt"),
        )
        albums_raw = raw.get("album", [])
        if isinstance(albums_raw, dict):
            albums_raw = [albums_raw]
        albums = [
            self._parse_album(a) for a in albums_raw if isinstance(a, dict) and a.get("id")
        ]
        return artist, albums

    async def get_album(self, album_id: str) -> tuple[SubsonicAlbum, list[SubsonicSong]]:
        """返回单个专辑及其歌曲列表。"""

        payload = await self._request("getAlbum.view", {"id": album_id})
        raw = payload.get("album", {})
        if isinstance(raw, list):
            raw = raw[0] if raw else {}
        if not isinstance(raw, dict):
            raw = {}
        album = self._parse_album(raw)
        songs_raw = raw.get("song", [])
        if isinstance(songs_raw, dict):
            songs_raw = [songs_raw]
        songs = [
            self._parse_song(s) for s in songs_raw if isinstance(s, dict) and s.get("id")
        ]
        return album, songs

    async def get_song(self, song_id: str) -> SubsonicSong:
        """返回单首歌曲详情。"""

        payload = await self._request("getSong.view", {"id": song_id})
        return self._parse_song(payload.get("song", {}))

    async def get_album_list2(
        self,
        type: str = "alphabeticalByName",
        size: int = 500,
        offset: int = 0,
        music_folder_id: int | None = None,
    ) -> list[SubsonicAlbum]:
        """按指定排序返回专辑列表（绕过艺术家维度，适合批量拉取）。"""

        params: dict[str, object] = {"type": type, "size": size, "offset": offset}
        if music_folder_id is not None:
            params["musicFolderId"] = music_folder_id
        payload = await self._request("getAlbumList2.view", params)
        albums = payload.get("albumList2", {}).get("album", [])
        return [self._parse_album(a) for a in albums]

    async def get_cover_art(self, cover_art_id: str, size: int | None = None) -> bytes:
        """直接取回封面图二进制（不走 JSON 解析）。"""

        params = {"id": cover_art_id}
        if size is not None:
            params["size"] = size
        url = f"{self._config.rest_base_url}/getCoverArt.view"
        query = self._auth_params()
        for key, value in params.items():
            query[key] = str(value)
        try:
            response = await self._http.get(url, params=query)
        except httpx.HTTPError as exc:
            raise SubsonicUnavailableError(detail=str(exc)) from exc
        if response.status_code >= 400:
            raise SubsonicUnavailableError(f"封面获取失败 HTTP {response.status_code}")
        return response.content

    # ------------------------------------------------------------------ 歌单
    async def get_playlists(self) -> list[SubsonicPlaylist]:
        """返回当前用户的歌单摘要列表。"""

        payload = await self._request("getPlaylists.view")
        raw_list = payload.get("playlists", {}).get("playlist", [])
        return [self._parse_playlist_summary(p) for p in raw_list]

    async def get_playlist(self, playlist_id: str) -> SubsonicPlaylist:
        """返回单个歌单详情（含歌曲 id 列表）。"""

        payload = await self._request("getPlaylist.view", {"id": playlist_id})
        return self._parse_playlist(payload.get("playlist", {}))

    async def create_playlist(
        self, name: str, song_ids: list[str], *, public: bool = False
    ) -> str:
        """新建歌单，返回新歌单的 id。

        Subsonic 的 ``createPlaylist.view`` 是 GET 端点，``songId`` 可重复出现。
        """

        payload = await self._request(
            "createPlaylist.view",
            {"name": name, "public": public, "songId": list(song_ids)},
        )
        return payload.get("playlist", {}).get("id", "")

    async def update_playlist(
        self,
        playlist_id: str,
        *,
        name: str | None = None,
        song_ids: list[str] | None = None,
        append_song_ids: list[str] | None = None,
    ) -> None:
        """修改歌单：改名、整体替换歌曲、或追加歌曲。

        - ``song_ids``：整体替换（逗号分隔单次参数）。
        - ``append_song_ids``：追加（``songIdToAdd`` 重复出现）。
        """

        params: dict[str, Any] = {"playlistId": playlist_id}
        if name is not None:
            params["name"] = name
        if song_ids is not None:
            params["songIds"] = ",".join(song_ids)
        if append_song_ids:
            params["songIdToAdd"] = list(append_song_ids)
        await self._request("updatePlaylist.view", params)

    async def delete_playlist(self, playlist_id: str) -> None:
        """删除歌单。"""

        await self._request("deletePlaylist.view", {"id": playlist_id})

    # ------------------------------------------------------------------ 解析辅助
    @staticmethod
    def _encode_param(value: object) -> str:
        if isinstance(value, bool):
            return str(value).lower()
        return str(value)

    @staticmethod
    def _parse_playlist_summary(raw: dict) -> SubsonicPlaylist:
        return SubsonicPlaylist(
            id=raw.get("id", ""),
            name=raw.get("name", ""),
            comment=raw.get("comment"),
            owner=raw.get("owner"),
            public=bool(raw.get("public", False)),
            song_count=int(raw.get("songCount", 0) or 0),
            duration=int(raw.get("duration", 0) or 0),
            cover_art=raw.get("coverArt"),
        )

    @staticmethod
    def _parse_playlist(raw: dict) -> SubsonicPlaylist:
        songs = raw.get("entry", [])
        song_ids = [s.get("id") for s in songs if isinstance(s, dict) and s.get("id")]

        def _to_dt(value: object) -> datetime | None:
            if not value:
                return None
            try:
                return datetime.fromtimestamp(float(value) / 1000.0, tz=timezone.utc)
            except (TypeError, ValueError):
                return None

        return SubsonicPlaylist(
            id=raw.get("id", ""),
            name=raw.get("name", ""),
            comment=raw.get("comment"),
            owner=raw.get("owner"),
            public=bool(raw.get("public", False)),
            song_count=int(raw.get("songCount", 0) or 0),
            duration=int(raw.get("duration", 0) or 0),
            cover_art=raw.get("coverArt"),
            song_ids=song_ids,
            created=_to_dt(raw.get("created")),
            changed=_to_dt(raw.get("changed")),
        )

    @staticmethod
    def _parse_album(raw: dict) -> SubsonicAlbum:
        artists = raw.get("artists") or []
        artist_name = raw.get("artist") or (artists[0].get("name") if artists else None)
        return SubsonicAlbum(
            id=raw["id"],
            name=raw.get("name", ""),
            artist_id=raw.get("artistId"),
            artist_name=artist_name,
            cover_art=raw.get("coverArt"),
            song_count=raw.get("songCount"),
            duration=raw.get("duration"),
            year=raw.get("year"),
            genre=raw.get("genre"),
        )

    @staticmethod
    def _parse_song(raw: dict) -> SubsonicSong:
        return SubsonicSong(
            id=raw["id"],
            title=raw.get("title", ""),
            album_id=raw.get("albumId"),
            album_name=raw.get("album"),
            artist_id=raw.get("artistId"),
            artist_name=raw.get("artist"),
            track=raw.get("track"),
            year=raw.get("year"),
            genre=raw.get("genre"),
            duration=raw.get("duration"),
            bit_rate=raw.get("bitRate"),
            size=raw.get("size"),
            content_type=raw.get("contentType"),
            suffix=raw.get("suffix"),
            path=raw.get("path"),
            cover_art=raw.get("coverArt"),
        )

"""音频流接口：把 Subsonic 的 ``stream.view`` 代理给前端，前端不持有 Subsonic 凭据。

支持 Range 转发（浏览器拖动进度条时的分段请求），并正确回传 206 / Content-Range，
做到「真能听、能拖动」。
"""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.api.deps import SubsonicSettingsServiceDep
from app.subsonic.client import SubsonicClient

router = APIRouter(prefix="/stream", tags=["stream"])


@router.get("/{song_id}", summary="按 Subsonic 歌曲 id 串流播放（代理）")
async def stream_song(
    song_id: str,
    request: Request,
    settings_service: SubsonicSettingsServiceDep,
    max_bit_rate: int | None = None,
) -> StreamingResponse:
    config = settings_service.resolve()
    if not config.is_complete:
        raise HTTPException(status_code=404, detail="Subsonic 未配置")

    client = SubsonicClient(config)
    try:
        upstream = await client.get_stream_response(
            song_id,
            max_bit_rate=max_bit_rate,
            range_header=request.headers.get("Range"),
        )
    except Exception as exc:  # 连接/超时等
        await client.aclose()
        raise HTTPException(status_code=502, detail=f"Subsonic 流获取失败：{exc}")

    status = upstream.status_code
    if status >= 400:
        body = await upstream.aread()
        await upstream.aclose()
        await client.aclose()
        raise HTTPException(status_code=502, detail=f"Subsonic 返回错误：{body[:200]}")

    media_type = upstream.headers.get("content-type") or "audio/mpeg"
    headers: dict[str, str] = {}
    for key in ("content-range", "accept-ranges", "content-length", "content-type"):
        if key in upstream.headers:
            headers[key] = upstream.headers[key]

    async def gen() -> AsyncGenerator[bytes, None]:
        try:
            async for chunk in upstream.aiter_bytes(chunk_size=65536):
                yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()

    return StreamingResponse(
        gen(),
        status_code=status,
        media_type=media_type,
        headers=headers,
    )

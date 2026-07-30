"""OpenAI 兼容 Provider。

覆盖 OpenAI 官方、DeepSeek、OpenRouter、硅基流动、本地 vLLM 等所有
兼容 ``/chat/completions`` 的接口——只需改 ``base_url`` 与 ``api_key``。
"""

from __future__ import annotations

from typing import Any

import httpx

from app.ai.providers.base import ChatRequest, ChatResponse, LLMProvider
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        *,
        timeout: float = 60.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._owns_client = client is None
        self._http = client or httpx.AsyncClient(timeout=timeout, follow_redirects=True)

    async def chat(self, request: ChatRequest) -> ChatResponse:
        payload: dict[str, Any] = {
            "model": request.model or self._model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.response_format is not None:
            payload["response_format"] = request.response_format

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        try:
            resp = await self._http.post(
                f"{self._base_url}/chat/completions", json=payload, headers=headers
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:300]
            raise RuntimeError(f"LLM 返回 {exc.response.status_code}: {body}") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"LLM 请求失败: {exc}") from exc

        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return ChatResponse(content=content, model=data.get("model", self._model), raw=data)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._http.aclose()

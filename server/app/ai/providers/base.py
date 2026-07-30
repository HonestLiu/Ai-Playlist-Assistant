"""LLM Provider 统一抽象。

所有大模型调用都只通过 ``LLMProvider.chat()`` 这一接口，业务层不感知
OpenAI / Gemini / Claude / Ollama 的差异。结构化输出（JSON）统一走
``chat_json()``，便于意图解析与候选选择复用同一套代码。
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["system", "user", "assistant"]


@dataclass
class Message:
    role: Role
    content: str


@dataclass
class ChatRequest:
    messages: list[Message]
    temperature: float = 0.7
    max_tokens: int | None = None
    model: str | None = None
    # OpenAI 风格的 JSON 模式：{"type": "json_object"} 或 {"type": "json_schema", ...}
    response_format: dict[str, Any] | None = None


@dataclass
class ChatResponse:
    content: str
    model: str
    raw: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """任意大模型提供方都实现这一接口。"""

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse: ...

    async def chat_json(self, request: ChatRequest) -> Any:
        """默认实现：调用 ``chat`` 并把返回文本解析成 JSON。"""

        resp = await self.chat(request)
        text = resp.content.strip()
        # 容忍模型偶尔包一层 ```json 代码块
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
        return json.loads(text)

"""Provider 工厂：根据配置实例化具体的 LLMProvider。"""

from __future__ import annotations

from app.ai.providers.base import LLMProvider
from app.ai.providers.mock_provider import MockProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.core.config import LLMSettings


def get_provider(settings: LLMSettings) -> LLMProvider:
    """按配置选择 Provider。

    - ``mock``：本地无 key 模式，直接返回 ``MockProvider``。
    - ``openai``（默认）：OpenAI 兼容接口，覆盖 DeepSeek/OpenRouter/硅基流动等。
    """

    provider = (settings.provider or "openai").lower()
    if provider == "mock":
        return MockProvider()
    if provider == "openai":
        key = settings.api_key.get_secret_value() if settings.api_key else ""
        return OpenAIProvider(
            base_url=settings.base_url,
            api_key=key,
            model=settings.model,
            timeout=60.0,
        )
    raise ValueError(f"不支持的 LLM provider: {settings.provider}")

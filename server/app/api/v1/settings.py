"""连接配置的读写与测试（Subsonic + LLM）。"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.ai.providers import ChatRequest, Message, get_provider
from app.api.deps import LLMSettingsServiceDep, SubsonicServiceDep, SubsonicSettingsServiceDep
from app.models.subsonic import ConnectionStatus
from app.schemas.settings import (
    LLMConfigIn,
    LLMConfigOut,
    LLMTestResult,
    SubsonicConfigIn,
    SubsonicConfigOut,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/subsonic", response_model=SubsonicConfigOut, summary="读取当前连接配置")
async def read_subsonic_config(
    settings_service: SubsonicSettingsServiceDep,
) -> SubsonicConfigOut:
    return settings_service.to_view()


@router.put("/subsonic", response_model=SubsonicConfigOut, summary="保存连接配置")
async def update_subsonic_config(
    payload: SubsonicConfigIn,
    settings_service: SubsonicSettingsServiceDep,
) -> SubsonicConfigOut:
    settings_service.save(payload)
    return settings_service.to_view()


@router.delete(
    "/subsonic",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="清除网页配置，回落到 .env",
)
async def reset_subsonic_config(settings_service: SubsonicSettingsServiceDep) -> Response:
    settings_service.reset()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/subsonic/test",
    response_model=ConnectionStatus,
    summary="测试连接（不保存）",
)
async def test_subsonic_config(
    payload: SubsonicConfigIn,
    settings_service: SubsonicSettingsServiceDep,
    subsonic_service: SubsonicServiceDep,
) -> ConnectionStatus:
    candidate = settings_service.build_candidate(payload)
    return await subsonic_service.check(candidate)


# ------------------------------------------------------------------ LLM
@router.get("/llm", response_model=LLMConfigOut, summary="读取当前 LLM 配置")
async def read_llm_config(settings_service: LLMSettingsServiceDep) -> LLMConfigOut:
    return settings_service.to_view()


@router.put("/llm", response_model=LLMConfigOut, summary="保存 LLM 配置")
async def update_llm_config(
    payload: LLMConfigIn, settings_service: LLMSettingsServiceDep
) -> LLMConfigOut:
    settings_service.save(payload)
    return settings_service.to_view()


@router.delete(
    "/llm",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="清除网页配置，回落到 .env",
)
async def reset_llm_config(settings_service: LLMSettingsServiceDep) -> Response:
    settings_service.reset()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/llm/test", response_model=LLMTestResult, summary="测试 LLM 连通（不保存）")
async def test_llm_config(
    payload: LLMConfigIn, settings_service: LLMSettingsServiceDep
) -> LLMTestResult:
    candidate = settings_service.build_candidate(payload)
    provider = get_provider(candidate)
    if candidate.provider == "mock":
        return LLMTestResult(provider="mock", ok=True, model="mock-local")
    try:
        resp = await provider.chat(
            ChatRequest(messages=[Message(role="user", content="ping")], max_tokens=8)
        )
        return LLMTestResult(
            provider=candidate.provider, ok=True, model=resp.model or candidate.model
        )
    except Exception as exc:  # noqa: BLE001
        return LLMTestResult(provider=candidate.provider, ok=False, error=str(exc)[:300])

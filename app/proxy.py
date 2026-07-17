"""OpenAI-compatible /v1/chat/completions proxy with system prompt injection."""

import json
from collections.abc import AsyncIterator
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from app.auth import verify_client_key
from app.config import load_prompts, settings

router = APIRouter(prefix="/v1", tags=["proxy"])


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str = Field(min_length=1)
    messages: list[dict[str, Any]]
    stream: bool = False


def _inject_system_prompt(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Prepend the configured system prompt to the message list."""
    config = load_prompts()
    system_text = (config.get("system_prompt") or "").strip()
    if not system_text:
        return messages

    # If the user already sent a system message, merge ours in front of it.
    if messages and messages[0].get("role") == "system":
        merged = {"role": "system", "content": system_text + "\n\n" + messages[0].get("content", "")}
        return [merged, *messages[1:]]

    return [{"role": "system", "content": system_text}, *messages]


def _override_model(model: str) -> str:
    """Allow the prompt config to force a specific upstream model."""
    forced = (load_prompts().get("force_model") or "").strip()
    return forced or model


@router.post("/chat/completions", response_model=None)
async def chat_completions(
    chat_request: ChatCompletionRequest,
    _token: Annotated[str, Depends(verify_client_key)],
):
    messages = _inject_system_prompt(chat_request.messages)
    model = _override_model(chat_request.model)

    payload = chat_request.model_dump(exclude_none=True)
    payload["model"] = model
    payload["messages"] = messages

    upstream_url = settings.upstream_base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.upstream_api_key}",
        "Content-Type": "application/json",
    }

    if chat_request.stream:
        return StreamingResponse(
            _stream_upstream(upstream_url, headers, payload),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(upstream_url, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Upstream request failed: {exc}",
            ) from exc

    if resp.is_error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"upstream_status": resp.status_code, "upstream_body": resp.text},
        )

    return JSONResponse(content=resp.json())


async def _stream_upstream(
    url: str, headers: dict, payload: dict
) -> AsyncIterator[str]:
    """Stream chunks from the upstream OpenAI-compatible endpoint."""
    timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                if resp.is_error:
                    body = await resp.aread()
                    err = json.dumps(
                        {"error": {"code": resp.status_code, "message": body.decode("utf-8", "replace")}}
                    )
                    yield f"data: {err}\n\n"
                    yield "data: [DONE]\n\n"
                    return
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data:"):
                        yield line + "\n\n"
                    else:
                        yield f"data: {line}\n\n"
        except httpx.HTTPError as exc:
            err = json.dumps({"error": {"code": 502, "message": f"stream error: {exc}"}})
            yield f"data: {err}\n\n"
        finally:
            yield "data: [DONE]\n\n"

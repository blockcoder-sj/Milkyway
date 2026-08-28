"""Natural language to validated strategy DSL through user-owned AI APIs."""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time

import httpx
from pydantic import ValidationError

from .ai_credentials import provider_requires_api_key, validate_api_key, validate_provider_model
from .strategies import StrategySpec, strategy_code_preview


logger = logging.getLogger("cloud_app.ai")
_local_status_lock = threading.Lock()
_local_status_cache: dict[str, object] = {
    "key": None,
    "expires_at": 0.0,
    "ready": False,
    "probing": False,
}

SYSTEM_PROMPT = """You translate Korean or English trading ideas into one JSON object.
Return JSON only, with no markdown. Never emit Python, shell, imports, URLs, or prose.
Allowed schema:
{
  "schema_version": 1,
  "name": "2-100 chars",
  "description": "plain description",
  "factors": [{"kind": one of ["momentum","mean_reversion","low_volatility","moving_average","volume_momentum","rsi"], "lookback": 2..252, "weight": -5..5}],
  "filters": {"min_price": 1..1000, "min_average_volume": 0..1000000000, "history_days": 20..252},
  "portfolio": {"initial_cash": 1000..10000000, "max_positions": 1..50, "rebalance_days": 1..30, "cost_per_side": 0..0.02, "stop_loss_pct": -0.50..-0.005 or null}
}
Use conservative defaults when omitted: $100,000, 10 positions, 10-day rebalance,
0.3% per side, -5% stop, $5 minimum price, 200,000 average shares, 60-day history.
Do not invent unsupported indicators. Explain unsupported details briefly in description.
"""


def _extract_object(text: str) -> dict:
    value = text.strip()
    if value.startswith("```"):
        value = value.replace("```json", "").replace("```", "").strip()
    start = value.find("{")
    end = value.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("AI response did not contain a JSON object")
    parsed = json.loads(value[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("AI response must be one JSON object")
    return parsed


class AiProviderError(RuntimeError):
    """A safe, user-facing provider failure."""


def local_ai_ready(
    *,
    base_url: str,
    model: str,
    api_key: str,
    cache_seconds: float = 15.0,
    timeout_seconds: float = 2.0,
) -> bool:
    """Check the fixed local server/model without fanning out per browser refresh."""
    key_fingerprint = hashlib.sha256(api_key.encode("utf-8")).digest() if api_key else b""
    cache_key = (base_url.rstrip("/"), model, key_fingerprint)
    now = time.monotonic()
    with _local_status_lock:
        if _local_status_cache["key"] == cache_key and now < float(
            _local_status_cache["expires_at"]
        ):
            return bool(_local_status_cache["ready"])
        if _local_status_cache["key"] == cache_key and _local_status_cache["probing"]:
            return bool(_local_status_cache["ready"])
        headers = {"Authorization": "Bearer " + api_key} if api_key else {}
        previous_ready = (
            bool(_local_status_cache["ready"])
            if _local_status_cache["key"] == cache_key
            else None
        )
        _local_status_cache.update(key=cache_key, probing=True)
    ready = False
    try:
        response = httpx.get(
            base_url.rstrip("/") + "/models",
            headers=headers,
            timeout=timeout_seconds,
            trust_env=False,
        )
        response.raise_for_status()
        model_ids = {
            item.get("id")
            for item in response.json().get("data", [])
            if isinstance(item, dict)
        }
        ready = model in model_ids
    except (httpx.HTTPError, AttributeError, TypeError, ValueError):
        ready = False
    with _local_status_lock:
        _local_status_cache.update(
            key=cache_key,
            expires_at=time.monotonic() + max(1.0, cache_seconds),
            ready=ready,
            probing=False,
        )
        if previous_ready is None or previous_ready != ready:
            logger.info("[local-ai] readiness ready=%s model=%s", ready, model)
        return ready


def _openai_text(payload: dict) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                return content["text"]
    raise ValueError("OpenAI response did not contain text")


def _anthropic_text(payload: dict) -> str:
    for content in payload.get("content", []):
        if content.get("type") == "text" and isinstance(content.get("text"), str):
            return content["text"]
    raise ValueError("Anthropic response did not contain text")


def _chat_completion_text(payload: dict) -> str:
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Local AI response did not contain text") from exc
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Local AI response did not contain text")
    return content


def _provider_request(
    client: httpx.Client,
    provider: str,
    model: str,
    api_key: str,
    prompt: str,
    local_base_url: str | None = None,
) -> str:
    if provider == "openai":
        response = client.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": "Bearer " + api_key},
            json={
                "model": model,
                "instructions": SYSTEM_PROMPT,
                "input": prompt,
                "max_output_tokens": 1200,
            },
        )
        response.raise_for_status()
        return _openai_text(response.json())
    if provider == "local":
        if not local_base_url:
            raise AiProviderError("로컬 AI 서버가 설정되지 않았습니다")
        headers = {"Authorization": "Bearer " + api_key} if api_key else {}
        response = client.post(
            local_base_url.rstrip("/") + "/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 1200,
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        return _chat_completion_text(response.json())
    response = client.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        json={
            "model": model,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1200,
            "temperature": 0.1,
        },
    )
    response.raise_for_status()
    return _anthropic_text(response.json())


def _safe_provider_error(exc: httpx.HTTPStatusError, provider: str) -> AiProviderError:
    status_code = exc.response.status_code
    if provider == "local":
        if status_code == 401:
            return AiProviderError("로컬 AI 서버 인증 설정을 확인해 주세요")
        if status_code == 429:
            return AiProviderError("로컬 AI가 사용 중입니다. 잠시 후 다시 시도해 주세요")
        return AiProviderError("로컬 AI 서버 요청에 실패했습니다. 운영 상태를 확인해 주세요")
    if status_code == 401:
        return AiProviderError("API 키가 올바르지 않습니다. 설정에서 다시 연결해 주세요")
    if status_code == 403:
        return AiProviderError("선택한 모델을 사용할 권한이 없습니다")
    if status_code == 404:
        return AiProviderError("선택한 AI 모델을 찾을 수 없습니다")
    if status_code == 429:
        return AiProviderError("AI API 사용 한도 또는 결제 한도를 확인해 주세요")
    return AiProviderError("AI 공급자 요청에 실패했습니다. 잠시 후 다시 시도해 주세요")


def generate_strategy(
    prompt: str,
    *,
    provider: str,
    model: str,
    api_key: str,
    timeout_seconds: int = 120,
    local_base_url: str | None = None,
) -> tuple[StrategySpec, str]:
    provider, model = validate_provider_model(provider, model)
    if provider_requires_api_key(provider):
        api_key = validate_api_key(api_key)
    prompt = prompt.strip()
    if len(prompt) < 5 or len(prompt) > 3000:
        raise ValueError("전략 설명은 5~3000자여야 합니다")
    logger.info("[ai] strategy generation started provider=%s model=%s", provider, model)
    try:
        with httpx.Client(
            timeout=float(timeout_seconds), trust_env=provider != "local"
        ) as client:
            content = _provider_request(
                client, provider, model, api_key, prompt, local_base_url=local_base_url
            )
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "[ai] provider rejected request provider=%s status=%d",
            provider,
            exc.response.status_code,
        )
        raise _safe_provider_error(exc, provider) from exc
    except httpx.RequestError as exc:
        logger.warning("[ai] provider unavailable provider=%s error=%s", provider, type(exc).__name__)
        raise AiProviderError("AI 공급자에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요") from exc
    try:
        spec = StrategySpec.model_validate(_extract_object(content))
    except (TypeError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        logger.warning("[ai] invalid strategy output provider=%s: %s", provider, type(exc).__name__)
        raise ValueError("AI가 안전한 전략 규격을 만들지 못했습니다. 설명을 더 구체적으로 입력해 주세요") from exc
    logger.info("[ai] validated strategy=%s factors=%d", spec.name, len(spec.factors))
    return spec, strategy_code_preview(spec)

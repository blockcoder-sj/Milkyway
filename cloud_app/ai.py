"""Natural language to validated strategy DSL through user-owned AI APIs."""

from __future__ import annotations

import json
import logging

import httpx
from pydantic import ValidationError

from .ai_credentials import validate_api_key, validate_provider_model
from .strategies import StrategySpec, strategy_code_preview


logger = logging.getLogger("cloud_app.ai")

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


def _provider_request(
    client: httpx.Client,
    provider: str,
    model: str,
    api_key: str,
    prompt: str,
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


def _safe_provider_error(exc: httpx.HTTPStatusError) -> AiProviderError:
    status_code = exc.response.status_code
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
) -> tuple[StrategySpec, str]:
    provider, model = validate_provider_model(provider, model)
    api_key = validate_api_key(api_key)
    prompt = prompt.strip()
    if len(prompt) < 5 or len(prompt) > 3000:
        raise ValueError("전략 설명은 5~3000자여야 합니다")
    logger.info("[ai] strategy generation started provider=%s model=%s", provider, model)
    try:
        with httpx.Client(timeout=float(timeout_seconds)) as client:
            content = _provider_request(client, provider, model, api_key, prompt)
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "[ai] provider rejected request provider=%s status=%d",
            provider,
            exc.response.status_code,
        )
        raise _safe_provider_error(exc) from exc
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

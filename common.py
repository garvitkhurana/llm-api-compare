"""Shared OpenRouter helpers for the learning harness."""

from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
URL = "https://openrouter.ai/api/v1/chat/completions"

# Chat / structured / gen-evals — free model is fine
MODEL_CHAT = os.environ.get(
    "OPENROUTER_MODEL_CHAT",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
)
# Tool-calling / agent / agent-evals — must support `tools`
MODEL_TOOLS = os.environ.get(
    "OPENROUTER_MODEL_TOOLS",
    "openai/gpt-oss-20b:free",
)

# Comma-separated fallbacks tried after primary exhausts retries
MODEL_CHAT_FALLBACKS = [
    m.strip()
    for m in os.environ.get(
        "OPENROUTER_MODEL_CHAT_FALLBACKS",
        "google/gemma-4-31b-it:free,openai/gpt-oss-20b:free",
    ).split(",")
    if m.strip()
]
MODEL_TOOLS_FALLBACKS = [
    m.strip()
    for m in os.environ.get(
        "OPENROUTER_MODEL_TOOLS_FALLBACKS",
        "google/gemma-4-31b-it:free,openrouter/free",
    ).split(",")
    if m.strip()
]

MAX_ATTEMPTS = 3
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 60
RETRY_STATUSES = {429, 502, 503}


def require_api_key() -> None:
    if not API_KEY:
        raise SystemExit("Set OPENROUTER_API_KEY in .env (see .env.example)")


def _model_chain(primary: str, *, tools: bool) -> list[str]:
    fallbacks = MODEL_TOOLS_FALLBACKS if tools else MODEL_CHAT_FALLBACKS
    seen: set[str] = set()
    chain: list[str] = []
    for mid in [primary, *fallbacks]:
        if mid not in seen:
            seen.add(mid)
            chain.append(mid)
    return chain


def _error_text(data: Any, response_text: str = "") -> str:
    if isinstance(data, dict) and data.get("error") is not None:
        err = data["error"]
        return err if isinstance(err, str) else json.dumps(err)
    if data:
        return str(data)
    return response_text or "unknown error"


def _is_retryable_body_error(data: Any) -> bool:
    text = _error_text(data).lower()
    needles = (
        "resourceexhausted",
        "rate",
        "overloaded",
        "temporarily",
        "timeout",
        "capacity",
        "try again",
    )
    return any(n in text for n in needles)


def _backoff_sleep(attempt: int) -> None:
    # attempt 0 → ~1s, 1 → ~2s, 2 → ~4s
    delay = (2**attempt) + random.uniform(0, 0.25)
    time.sleep(delay)


def chat(
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    stop: list[str] | None = None,
    temperature: float = 0.2,
    max_tokens: int = 600,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: Any = None,
) -> dict[str, Any]:
    """POST chat/completions with retries, backoff, and free-model fallbacks."""
    require_api_key()
    primary = model or MODEL_CHAT
    use_tools = tools is not None
    models = _model_chain(primary, tools=use_tools)
    last_error: Exception | None = None

    for model_i, mid in enumerate(models):
        if model_i > 0:
            print(f"[common.chat] fallback model → {mid}")

        for attempt in range(MAX_ATTEMPTS):
            payload: dict[str, Any] = {
                "model": mid,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if stop:
                payload["stop"] = stop
            if tools is not None:
                payload["tools"] = tools
            if tool_choice is not None:
                payload["tool_choice"] = tool_choice

            try:
                r = requests.post(
                    URL,
                    headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                )
            except (requests.Timeout, requests.ConnectionError) as e:
                last_error = e
                if attempt + 1 < MAX_ATTEMPTS:
                    print(
                        f"[common.chat] retry {attempt + 2}/{MAX_ATTEMPTS} "
                        f"after {type(e).__name__} on {mid}"
                    )
                    _backoff_sleep(attempt)
                    continue
                break

            data: Any = {}
            try:
                data = r.json() if r.content else {}
            except ValueError:
                data = {}

            if r.status_code in (401, 403):
                raise RuntimeError(
                    f"HTTP {r.status_code} (not retrying): {_error_text(data, r.text)}"
                )

            if r.status_code == 400 and not _is_retryable_body_error(data):
                raise RuntimeError(
                    f"HTTP 400 (not retrying): {_error_text(data, r.text)}"
                )

            ok = r.ok and "error" not in (data or {}) and bool(
                isinstance(data, dict) and data.get("choices")
            )
            if ok:
                return data

            retryable = (
                r.status_code in RETRY_STATUSES
                or _is_retryable_body_error(data)
                or (r.ok and isinstance(data, dict) and "error" in data)
            )
            last_error = RuntimeError(
                f"HTTP {r.status_code}: {_error_text(data, r.text)}"
            )

            if retryable and attempt + 1 < MAX_ATTEMPTS:
                print(
                    f"[common.chat] retry {attempt + 2}/{MAX_ATTEMPTS} "
                    f"after HTTP {r.status_code} on {mid}"
                )
                _backoff_sleep(attempt)
                continue
            break

    raise RuntimeError(
        f"OpenRouter failed after retries/fallbacks for models {models}: {last_error}"
    )


def choice_message(data: dict[str, Any]) -> dict[str, Any]:
    return data["choices"][0].get("message") or {}


def choice_text(data: dict[str, Any]) -> str:
    return choice_message(data).get("content") or ""


def finish_reason(data: dict[str, Any]) -> str | None:
    return data["choices"][0].get("finish_reason")


def usage(data: dict[str, Any]) -> dict[str, Any] | None:
    return data.get("usage")


def usage_breakdown(data: dict[str, Any]) -> dict[str, Any]:
    """
    Pricing-relevant token slice.

    OpenRouter/OpenAI-style:
      - prompt_tokens      ≈ input (what you send)
      - completion_tokens  ≈ output bill bucket (often includes reasoning)
      - reasoning_tokens   ≈ "thinking" (inside completion_tokens_details when present)
      - total_tokens       ≈ prompt + completion (usual)

    Visible answer text is NOT the same as completion_tokens when the model reasons.
    """
    u = usage(data) or {}
    details = u.get("completion_tokens_details") or {}
    prompt = u.get("prompt_tokens")
    completion = u.get("completion_tokens")
    reasoning = details.get("reasoning_tokens")
    total = u.get("total_tokens")

    # Best-effort: visible ≈ completion - reasoning when both are numbers
    visible = None
    if isinstance(completion, int) and isinstance(reasoning, int):
        visible = max(completion - reasoning, 0)

    return {
        "input_prompt_tokens": prompt,
        "output_completion_tokens": completion,
        "thinking_reasoning_tokens": reasoning,
        "visible_estimate": visible,
        "total_tokens": total,
        "cost": u.get("cost"),
        "raw": u,
    }


def print_usage(data: dict[str, Any]) -> None:
    b = usage_breakdown(data)
    print("tokens (pricing view):")
    print(f"  input    (prompt):     {b['input_prompt_tokens']}")
    print(f"  output   (completion): {b['output_completion_tokens']}")
    print(f"  thinking (reasoning):  {b['thinking_reasoning_tokens']}")
    print(f"  visible  (est.):       {b['visible_estimate']}")
    print(f"  total:                 {b['total_tokens']}")
    if b.get("cost") is not None:
        print(f"  cost (API field):      {b['cost']}")


def pretty(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)

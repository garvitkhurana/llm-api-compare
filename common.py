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

# openrouter (default) | anthropic — use Anthropic when OpenRouter free quota is dead
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openrouter").strip().lower()

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
URL = "https://openrouter.ai/api/v1/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

# Chat / structured / gen-evals
MODEL_CHAT = os.environ.get(
    "OPENROUTER_MODEL_CHAT",
    "openai/gpt-oss-20b:free",
)
# Tool-calling / agent / agent-evals — must support `tools`
MODEL_TOOLS = os.environ.get(
    "OPENROUTER_MODEL_TOOLS",
    "openai/gpt-oss-20b:free",
)
# Used when LLM_PROVIDER=anthropic
ANTHROPIC_MODEL = os.environ.get(
    "ANTHROPIC_MODEL",
    "claude-haiku-4-5",
)

# Comma-separated fallbacks tried after primary exhausts retries (OpenRouter only)
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
    if LLM_PROVIDER == "anthropic":
        if not ANTHROPIC_API_KEY:
            raise SystemExit("Set ANTHROPIC_API_KEY in .env (LLM_PROVIDER=anthropic)")
        return
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


def _is_daily_free_quota(data: Any) -> bool:
    """OpenRouter free-models-per-day — retries/fallbacks won't help until reset."""
    text = _error_text(data).lower()
    return "free-models-per-day" in text or "free model requests per day" in text


def _backoff_sleep(attempt: int) -> None:
    # attempt 0 → ~1s, 1 → ~2s, 2 → ~4s
    delay = (2**attempt) + random.uniform(0, 0.25)
    time.sleep(delay)


def _openai_tools_to_anthropic(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for t in tools:
        fn = t.get("function") or t
        out.append(
            {
                "name": fn["name"],
                "description": fn.get("description") or "",
                "input_schema": fn.get("parameters")
                or {"type": "object", "properties": {}},
            }
        )
    return out


def _messages_to_anthropic(
    messages: list[dict[str, Any]],
) -> tuple[str | None, list[dict[str, Any]]]:
    """Convert OpenAI-style messages to Anthropic system + messages."""
    system_parts: list[str] = []
    out: list[dict[str, Any]] = []

    for m in messages:
        role = m.get("role")
        if role == "system":
            system_parts.append(str(m.get("content") or ""))
            continue

        if role == "user":
            out.append({"role": "user", "content": m.get("content") or ""})
            continue

        if role == "assistant":
            blocks: list[dict[str, Any]] = []
            text = m.get("content")
            if text:
                blocks.append({"type": "text", "text": text})
            for tc in m.get("tool_calls") or []:
                fn = tc.get("function") or {}
                raw = fn.get("arguments") or "{}"
                try:
                    args = json.loads(raw) if isinstance(raw, str) else raw
                except json.JSONDecodeError:
                    args = {}
                blocks.append(
                    {
                        "type": "tool_use",
                        "id": tc.get("id") or "tool",
                        "name": fn.get("name") or "",
                        "input": args,
                    }
                )
            if not blocks:
                blocks = [{"type": "text", "text": ""}]
            out.append({"role": "assistant", "content": blocks})
            continue

        if role == "tool":
            # Anthropic wants tool_result inside a user message
            block = {
                "type": "tool_result",
                "tool_use_id": m.get("tool_call_id") or "",
                "content": str(m.get("content") or ""),
            }
            if out and out[-1].get("role") == "user" and isinstance(
                out[-1].get("content"), list
            ):
                out[-1]["content"].append(block)
            else:
                out.append({"role": "user", "content": [block]})
            continue

    system = "\n\n".join(p for p in system_parts if p).strip() or None
    return system, out


def _anthropic_to_openai_shape(data: dict[str, Any], model: str) -> dict[str, Any]:
    """Normalize Anthropic Messages response to OpenAI chat.completion shape."""
    content_blocks = data.get("content") or []
    texts: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    for b in content_blocks:
        if not isinstance(b, dict):
            continue
        if b.get("type") == "text":
            texts.append(b.get("text") or "")
        elif b.get("type") == "tool_use":
            tool_calls.append(
                {
                    "id": b.get("id"),
                    "type": "function",
                    "function": {
                        "name": b.get("name"),
                        "arguments": json.dumps(b.get("input") or {}),
                    },
                }
            )

    stop = data.get("stop_reason")
    finish = "tool_calls" if tool_calls or stop == "tool_use" else "stop"
    msg: dict[str, Any] = {
        "role": "assistant",
        "content": "\n".join(texts) if texts else None,
    }
    if tool_calls:
        msg["tool_calls"] = tool_calls

    usage_in = data.get("usage") or {}
    return {
        "id": data.get("id"),
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": msg,
                "finish_reason": finish,
            }
        ],
        "usage": {
            "prompt_tokens": usage_in.get("input_tokens"),
            "completion_tokens": usage_in.get("output_tokens"),
            "total_tokens": (usage_in.get("input_tokens") or 0)
            + (usage_in.get("output_tokens") or 0),
        },
        "provider": "anthropic",
    }


def _chat_anthropic(
    messages: list[dict[str, Any]],
    *,
    model: str,
    temperature: float,
    max_tokens: int,
    tools: list[dict[str, Any]] | None,
    tool_choice: Any,
) -> dict[str, Any]:
    system, anth_messages = _messages_to_anthropic(messages)
    payload: dict[str, Any] = {
        "model": model,
        "messages": anth_messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if system:
        payload["system"] = system
    if tools is not None:
        payload["tools"] = _openai_tools_to_anthropic(tools)
        if tool_choice == "auto" or tool_choice is None:
            payload["tool_choice"] = {"type": "auto"}
        elif tool_choice == "required":
            payload["tool_choice"] = {"type": "any"}
        elif isinstance(tool_choice, dict):
            payload["tool_choice"] = tool_choice

    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            r = requests.post(
                ANTHROPIC_URL,
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
        except (requests.Timeout, requests.ConnectionError) as e:
            last_error = e
            if attempt + 1 < MAX_ATTEMPTS:
                print(
                    f"[common.chat] anthropic retry {attempt + 2}/{MAX_ATTEMPTS} "
                    f"after {type(e).__name__}",
                    flush=True,
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
                f"Anthropic HTTP {r.status_code}: {_error_text(data, r.text)}"
            )
        if r.ok and isinstance(data, dict) and data.get("content") is not None:
            return _anthropic_to_openai_shape(data, model)

        last_error = RuntimeError(
            f"Anthropic HTTP {r.status_code}: {_error_text(data, r.text)}"
        )
        if r.status_code in RETRY_STATUSES and attempt + 1 < MAX_ATTEMPTS:
            print(
                f"[common.chat] anthropic retry {attempt + 2}/{MAX_ATTEMPTS} "
                f"after HTTP {r.status_code}",
                flush=True,
            )
            _backoff_sleep(attempt)
            continue
        break

    raise RuntimeError(f"Anthropic failed: {last_error}")


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
    """POST chat/completions (OpenRouter) or Messages (Anthropic)."""
    require_api_key()

    if LLM_PROVIDER == "anthropic":
        mid = model if model and not model.endswith(":free") else ANTHROPIC_MODEL
        # Ignore OpenRouter free model ids when on Anthropic
        if "/" in mid and mid.split("/", 1)[0] in {
            "openai",
            "google",
            "nvidia",
            "openrouter",
            "meta-llama",
        }:
            mid = ANTHROPIC_MODEL
        print(f"[common.chat] provider=anthropic model={mid}", flush=True)
        return _chat_anthropic(
            messages,
            model=mid,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            tool_choice=tool_choice,
        )

    primary = model or MODEL_CHAT
    use_tools = tools is not None
    models = _model_chain(primary, tools=use_tools)
    last_error: Exception | None = None

    for model_i, mid in enumerate(models):
        if model_i > 0:
            print(f"[common.chat] fallback model → {mid}", flush=True)

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
                        f"after {type(e).__name__} on {mid}",
                        flush=True,
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

            # Prefer body text; also catch daily free cap via headers
            remaining = r.headers.get("X-RateLimit-Remaining")
            if _is_daily_free_quota(data) or (
                r.status_code == 429
                and remaining == "0"
                and "free" in _error_text(data, r.text).lower()
            ):
                raise RuntimeError(
                    "OpenRouter free-models-per-day quota exhausted "
                    "(retries won't help). Wait for daily reset, add credits, "
                    f"or use a paid model. Detail: {_error_text(data, r.text)}"
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
                    f"after HTTP {r.status_code} on {mid}",
                    flush=True,
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

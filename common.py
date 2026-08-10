"""Shared OpenRouter helpers for the learning harness."""

from __future__ import annotations

import json
import os
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
    "openrouter/free",
)


def require_api_key() -> None:
    if not API_KEY:
        raise SystemExit("Set OPENROUTER_API_KEY in .env (see .env.example)")


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
    """POST chat/completions. Returns the full JSON body (not just text)."""
    require_api_key()
    payload: dict[str, Any] = {
        "model": model or MODEL_CHAT,
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

    r = requests.post(
        URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    data = r.json() if r.content else {}
    if not r.ok or "error" in data or not data.get("choices"):
        raise RuntimeError(data.get("error") or data or r.text)
    return data


def choice_message(data: dict[str, Any]) -> dict[str, Any]:
    return data["choices"][0].get("message") or {}


def choice_text(data: dict[str, Any]) -> str:
    return choice_message(data).get("content") or ""


def finish_reason(data: dict[str, Any]) -> str | None:
    return data["choices"][0].get("finish_reason")


def usage(data: dict[str, Any]) -> dict[str, Any] | None:
    return data.get("usage")


def pretty(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)

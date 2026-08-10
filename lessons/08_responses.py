"""08 — Anatomy of a chat completion response."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import MODEL_CHAT, MODEL_TOOLS, chat, pretty, print_usage
from tools import TOOL_SPECS


def show(label: str, data: dict) -> None:
    choice = data["choices"][0]
    msg = choice.get("message") or {}
    print("=" * 60)
    print(label)
    print("finish_reason:", choice.get("finish_reason"))
    print_usage(data)
    print("content:", msg.get("content"))
    print("tool_calls:", pretty(msg.get("tool_calls")))


def main() -> None:
    plain = chat(
        [{"role": "user", "content": "Say hi in 3 words."}],
        model=MODEL_CHAT,
        max_tokens=32,
    )
    show("plain chat", plain)

    tools = chat(
        [{"role": "user", "content": "Use calculator for 1+1."}],
        model=MODEL_TOOLS,
        tools=TOOL_SPECS,
        temperature=0,
        max_tokens=200,
    )
    show("with tools", tools)


if __name__ == "__main__":
    main()

"""05 — Model requests a tool; you execute; you return the result."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import MODEL_TOOLS, chat, choice_message, finish_reason, pretty
from tools import TOOL_SPECS, run_tool


def main() -> None:
    messages = [
        {
            "role": "user",
            "content": "Use the calculator tool to compute (17 + 4) * 3. Then state the value.",
        }
    ]
    data = chat(
        messages,
        model=MODEL_TOOLS,
        tools=TOOL_SPECS,
        tool_choice="auto",
        temperature=0,
        max_tokens=400,
    )
    msg = choice_message(data)
    print("model:", data.get("model") or MODEL_TOOLS)
    print("finish_reason:", finish_reason(data))
    print("assistant content:", msg.get("content"))
    print("tool_calls:", pretty(msg.get("tool_calls")))

    tool_calls = msg.get("tool_calls") or []
    if not tool_calls:
        print("\nNo tool_calls — try another OPENROUTER_MODEL_TOOLS.")
        return

    messages.append(msg)
    for tc in tool_calls:
        fn = tc.get("function") or {}
        name = fn.get("name") or ""
        args = fn.get("arguments") or "{}"
        result = run_tool(name, args)
        print(f"\nran {name}({args}) -> {result}")
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tc.get("id"),
                "name": name,
                "content": result,
            }
        )

    data2 = chat(
        messages,
        model=MODEL_TOOLS,
        tools=TOOL_SPECS,
        temperature=0,
        max_tokens=200,
    )
    print("\nfinal:", choice_message(data2).get("content"))


if __name__ == "__main__":
    main()

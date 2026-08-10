"""05 — Model requests a tool; you execute; you return the result."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import MODEL_TOOLS, chat, choice_message, pretty
from tools import TOOL_SPECS, run_tool

MAX_ROUNDS = 6  # some models call one tool per turn


def main() -> None:
    messages = [
        {
            "role": "user",
            "content": (
                "Use tools for all of the following, then summarize the results:\n"
                "1) calculator: compute (17 + 4) * 3\n"
                "2) reverse_string: reverse the text 'hello world'\n"
                "3) word_stats: analyze the text 'hello world from lesson 05'\n"
                "Call every tool you need before answering."
            ),
        }
    ]

    for round_i in range(1, MAX_ROUNDS + 1):
        data = chat(
            messages,
            model=MODEL_TOOLS,
            tools=TOOL_SPECS,
            tool_choice="auto",
            temperature=0,
            max_tokens=600,
        )
        msg = choice_message(data)

        print(f"round {round_i} raw")
        print("---")
        print(pretty(data))
        print("---")

        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            print("final")
            print("---")
            print(msg.get("content"))
            return

        messages.append(msg)
        print(f"round {round_i} tools (local)")
        print("---")
        for tc in tool_calls:
            fn = tc.get("function") or {}
            name = fn.get("name") or ""
            args = fn.get("arguments") or "{}"
            result = run_tool(name, args)
            print(f"ran {name}({args}) -> {result}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.get("id"),
                    "name": name,
                    "content": result,
                }
            )
        print("---")

    print(f"stop — hit MAX_ROUNDS={MAX_ROUNDS}")


if __name__ == "__main__":
    main()

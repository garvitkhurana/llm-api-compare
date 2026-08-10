"""05 — Model requests a tool; you execute; you return the result."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import MODEL_TOOLS, chat, choice_message, finish_reason, pretty
from tools import TOOL_SPECS, list_tools, run_tool

SEP = "=" * 60
MAX_ROUNDS = 6  # some models call one tool per turn


def banner(title: str) -> None:
    print(f"\n{SEP}\n{title}\n{SEP}")


def _short(text: str | None, n: int = 72) -> str:
    if not text:
        return ""
    one = " ".join(text.split())
    return one if len(one) <= n else one[: n - 1] + "…"


def print_memory(messages: list[dict]) -> None:
    """High-level final conversation history."""
    banner(f"FINAL CONVO MEMORY ({len(messages)} msgs)")
    for i, m in enumerate(messages, 1):
        role = m.get("role") or "?"
        if role == "user":
            print(f"  {i}. user: {_short(m.get('content'))}")
        elif role == "assistant":
            tcs = m.get("tool_calls") or []
            if tcs:
                names = [
                    (tc.get("function") or {}).get("name") or "?" for tc in tcs
                ]
                print(f"  {i}. assistant → tools: {', '.join(names)}")
            else:
                print(f"  {i}. assistant: {_short(m.get('content'))}")
        elif role == "tool":
            print(
                f"  {i}. tool/{m.get('name')}: {_short(str(m.get('content')))}"
            )
        else:
            print(f"  {i}. {role}: {_short(str(m.get('content')))}")


def main() -> None:
    banner("AVAILABLE TOOLS (from DISPATCH / TOOL_SPECS)")
    print(pretty(list_tools()))

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

    banner("INITIAL REQUEST")
    print(pretty(messages))

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

        banner(f"ROUND {round_i} — full raw response")
        print(pretty(data))
        banner(f"ROUND {round_i} — highlights")
        print("model:", data.get("model") or MODEL_TOOLS)
        print("finish_reason:", finish_reason(data))
        print("assistant content:", msg.get("content"))
        print("tool_calls:", pretty(msg.get("tool_calls")))

        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            messages.append(msg)
            banner("FINAL ANSWER")
            print(msg.get("content"))
            print_memory(messages)
            return

        messages.append(msg)
        banner(f"ROUND {round_i} — local tool runs (your Python, not the model)")
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

        banner(f"ROUND {round_i} — messages after tools")
        print(pretty(messages))

    banner("STOP")
    print(f"Hit MAX_ROUNDS={MAX_ROUNDS} still requesting tools.")
    print_memory(messages)


if __name__ == "__main__":
    main()

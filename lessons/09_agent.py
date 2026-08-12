"""09 — Minimal agent loop (multi-step tools)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent import run_agent, tools_used
from common import pretty

SEP = "=" * 60


def banner(title: str) -> None:
    print(f"\n{SEP}\n{title}\n{SEP}")


def _short_messages(messages: list[dict]) -> list[str]:
    lines = []
    for i, m in enumerate(messages, 1):
        role = m.get("role") or "?"
        if role == "assistant" and m.get("tool_calls"):
            names = [
                (tc.get("function") or {}).get("name") or "?"
                for tc in m["tool_calls"]
            ]
            lines.append(f"  {i}. assistant → tools: {', '.join(names)}")
        elif role == "tool":
            content = str(m.get("content") or "")
            if len(content) > 72:
                content = content[:71] + "…"
            lines.append(f"  {i}. tool/{m.get('name')}: {content}")
        else:
            content = " ".join(str(m.get("content") or "").split())
            if len(content) > 72:
                content = content[:71] + "…"
            lines.append(f"  {i}. {role}: {content}")
    return lines


def main() -> None:
    task = (
        "1) Use calculator for (10 + 5) * 2. "
        "2) Use word_stats on the text 'agent loop'. "
        "3) Reply with both results in one short sentence."
    )

    def on_step(event: dict) -> None:
        kind = event.get("type")
        if kind == "llm":
            banner(f"LLM round {event['round']} — highlights")
            print(
                f"finish={event['finish_reason']}  "
                f"tool_calls={event['n_tool_calls']}"
            )
            banner(f"LLM round {event['round']} — raw API response")
            print(pretty(event["raw"]))
        elif kind == "tool":
            banner(
                f"TOOL (llm round {event['round']}) — {event['tool']}"
            )
            print("arguments (raw from model):", event["arguments"])
            print("result (raw from run_tool):", event["result"])
            print("tool_call object:")
            print(pretty(event.get("tool_call")))
        elif kind == "messages":
            banner(f"MESSAGES after llm round {event['round']} tools")
            print("\n".join(_short_messages(event["messages"])))
        elif kind == "final":
            banner(f"FINAL after {event['step_count']} LLM round(s)")
            print(event.get("final"))

    result = run_agent(task, max_steps=6, on_step=on_step)
    print("\ntools_used:", tools_used(result["steps"]))
    print("step_count (LLM rounds):", result["step_count"])
    print("finish_reason:", result["finish_reason"])
    if result.get("error"):
        print("error:", result["error"])


if __name__ == "__main__":
    main()

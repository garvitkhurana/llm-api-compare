"""09 — Minimal agent loop (multi-step tools)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent import run_agent, tools_used


def main() -> None:
    task = (
        "1) Use calculator for (10 + 5) * 2. "
        "2) Use word_stats on the text 'agent loop'. "
        "3) Reply with both results in one short sentence."
    )

    def on_step(event: dict) -> None:
        kind = event.get("type")
        if kind == "llm":
            print(
                f"[llm] round {event['round']} "
                f"(finish={event['finish_reason']}, tool_calls={event['n_tool_calls']})"
            )
        elif kind == "tool":
            print(
                f"[tool] (in llm round {event['round']}) "
                f"{event['tool']}({event['arguments']}) -> {event['result']}"
            )
        elif kind == "final":
            print(f"[final] after {event['step_count']} LLM round(s)")

    result = run_agent(task, max_steps=6, on_step=on_step)
    print("\ntools_used:", tools_used(result["steps"]))
    print("step_count (LLM rounds):", result["step_count"])
    print("finish_reason:", result["finish_reason"])
    print("final:", result["final"])
    if result.get("error"):
        print("error:", result["error"])


if __name__ == "__main__":
    main()

"""Minimal tool-calling agent loop (lessons 09 + 11). No frameworks."""

from __future__ import annotations

from typing import Any, Callable

from common import MODEL_TOOLS, chat, choice_message, finish_reason
from tools import TOOL_SPECS, run_tool


def run_agent(
    user_task: str,
    *,
    max_steps: int = 5,
    model: str | None = None,
    tools: list[dict[str, Any]] | None = None,
    system: str = "Solve the task. Use tools when helpful. Be brief.",
    on_step: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """
    Loop: model → tool_calls? execute & continue : return final text.
    Returns {final, steps, messages, finish_reason}.
    """
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_task},
    ]
    steps: list[dict[str, Any]] = []
    tool_list = tools if tools is not None else TOOL_SPECS

    for step_i in range(max_steps):
        data = chat(
            messages,
            model=model or MODEL_TOOLS,
            tools=tool_list,
            temperature=0.1,
            max_tokens=800,
        )
        msg = choice_message(data)
        fr = finish_reason(data)
        tool_calls = msg.get("tool_calls") or []

        assistant_msg: dict[str, Any] = {"role": "assistant", "content": msg.get("content")}
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
        messages.append(assistant_msg)

        if not tool_calls:
            result = {
                "final": msg.get("content") or "",
                "steps": steps,
                "messages": messages,
                "finish_reason": fr,
                "step_count": step_i + 1,
            }
            if on_step:
                on_step({"type": "final", **result})
            return result

        for tc in tool_calls:
            fn = tc.get("function") or {}
            name = fn.get("name") or ""
            raw_args = fn.get("arguments") or "{}"
            out = run_tool(name, raw_args)
            step = {
                "step": step_i,
                "tool": name,
                "arguments": raw_args,
                "result": out,
                "tool_call_id": tc.get("id"),
            }
            steps.append(step)
            if on_step:
                on_step({"type": "tool", **step})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.get("id"),
                    "name": name,
                    "content": out,
                }
            )

    return {
        "final": "",
        "steps": steps,
        "messages": messages,
        "finish_reason": "max_steps",
        "step_count": max_steps,
        "error": "hit max_steps without a final answer",
    }


def tools_used(steps: list[dict[str, Any]]) -> list[str]:
    return [s["tool"] for s in steps]

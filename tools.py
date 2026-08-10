"""Plain Python tools — no LLM, no MCP. Lesson 04 calls these directly."""

from __future__ import annotations

import json
from typing import Any


def word_stats(text: str) -> dict[str, int]:
    """Count words, characters, and lines in text."""
    return {
        "words": len(text.split()),
        "chars": len(text),
        "lines": text.count("\n") + (1 if text else 0),
    }


def calculator(expression: str) -> dict[str, Any]:
    """Evaluate a simple arithmetic expression (digits and + - * / ( ) . only)."""
    allowed = set("0123456789+-*/().% ")
    if not expression or any(c not in allowed for c in expression):
        return {"ok": False, "error": "only simple arithmetic allowed", "expression": expression}
    try:
        value = float(eval(expression, {"__builtins__": {}}, {}))  # noqa: S307
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e), "expression": expression}
    return {"ok": True, "expression": expression, "value": value}


TOOL_SPECS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "word_stats",
            "description": "Count words, characters, and lines in a text string.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to analyze"},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a simple arithmetic expression like '2 + 2 * 3'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Arithmetic expression",
                    },
                },
                "required": ["expression"],
            },
        },
    },
]

DISPATCH = {
    "word_stats": lambda args: word_stats(**args),
    "calculator": lambda args: calculator(**args),
}


def run_tool(name: str, arguments: str | dict[str, Any]) -> str:
    """Execute a tool by name; return JSON string for the model."""
    if isinstance(arguments, str):
        args = json.loads(arguments or "{}")
    else:
        args = arguments
    if name not in DISPATCH:
        return json.dumps({"ok": False, "error": f"unknown tool: {name}"})
    return json.dumps(DISPATCH[name](args))

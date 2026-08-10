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


def reverse_string(string: str) -> str:
    """Reverse a string."""
    return string[::-1]

def list_tools() -> list[dict[str, Any]]:
    """List all tools."""
    return [name for name in DISPATCH.keys()]


TOOL_SPECS = [
  {
    "type": "function",
    "function": {
      "name": "word_stats",
      "description": "Count words, characters, and lines in text.",
      "parameters": {
        "type": "object",
        "properties": {
          "text": {
            "type": "string",
            "description": "The text to analyze."
          }
        },
        "required": ["text"],
        "additionalProperties": False
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "calculator",
      "description": "Evaluate a simple arithmetic expression using digits and +, -, *, /, %, parentheses, and decimal points.",
      "parameters": {
        "type": "object",
        "properties": {
          "expression": {
            "type": "string",
            "description": "A simple arithmetic expression to evaluate."
          }
        },
        "required": ["expression"],
        "additionalProperties": False
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "reverse_string",
      "description": "Reverse a string.",
      "parameters": {
        "type": "object",
        "properties": {
          "string": {
            "type": "string",
            "description": "The string to reverse."
          }
        },
        "required": ["string"],
        "additionalProperties": False
      }
    }
  }
]

DISPATCH = {
    "word_stats": lambda args: word_stats(**args),
    "calculator": lambda args: calculator(**args),
    "reverse_string": lambda args: reverse_string(**args),
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

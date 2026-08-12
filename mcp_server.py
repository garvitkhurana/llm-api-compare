"""stdio MCP server exposing tools.py (lesson 06).

Do NOT run this interactively in a terminal — it speaks JSON-RPC on stdin/stdout.
Use:  python lessons/06_mcp.py
Or wire mcp_server.py into Cursor MCP settings (see README).
"""

from __future__ import annotations

import json
import sys

from mcp.server.fastmcp import FastMCP

from tools import calculator, reverse_string, word_stats

mcp = FastMCP("llm-harness-tools")


@mcp.tool()
def word_stats_tool(text: str) -> str:
    """Count words, characters, and lines in text."""
    return json.dumps(word_stats(text))


@mcp.tool()
def calculator_tool(expression: str) -> str:
    """Evaluate a simple arithmetic expression like '2 + 2 * 3'."""
    return json.dumps(calculator(expression))


@mcp.tool()
def reverse_string_tool(string: str) -> str:
    """Reverse a string."""
    return json.dumps(reverse_string(string))

@mcp.resource("lesson://resources")
def lesson_resources() -> str:
    """Short curriculum blurb (read-only data)."""
    return "run_tool(...) ->  await session.call_tool(name, args)"

@mcp.resource("lesson://resources/{resource_name}")
def lesson_resource(resource_name: str) -> str:
    """Resource by name (templated URI)."""
    return f"Resource {resource_name} content."


if __name__ == "__main__":
    if sys.stdin.isatty():
        print(
            "mcp_server.py is a stdio JSON-RPC server — not an interactive CLI.\n"
            "  Run the client lesson:  python lessons/06_mcp.py\n"
            "  Or add it under Cursor Settings → MCP (see README).",
            file=sys.stderr,
        )
        raise SystemExit(1)
    mcp.run(transport="stdio")

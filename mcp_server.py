"""stdio MCP server exposing tools.py (lesson 06)."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from tools import calculator, word_stats

mcp = FastMCP("llm-harness-tools")


@mcp.tool()
def word_stats_tool(text: str) -> str:
    """Count words, characters, and lines in text."""
    return json.dumps(word_stats(text))


@mcp.tool()
def calculator_tool(expression: str) -> str:
    """Evaluate a simple arithmetic expression like '2 + 2 * 3'."""
    return json.dumps(calculator(expression))


if __name__ == "__main__":
    mcp.run(transport="stdio")

"""06 — Call the same tools via MCP (list_tools + call_tool)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "mcp_server.py"


async def main() -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER)],
        cwd=str(ROOT),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("tools:")
            for t in tools.tools:
                print(f"  - {t.name}: {t.description}")

            result = await session.call_tool(
                "word_stats_tool",
                {"text": "hello via MCP"},
            )
            print("\ncall word_stats_tool ->", result.content)


if __name__ == "__main__":
    asyncio.run(main())

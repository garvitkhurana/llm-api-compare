"""06 — Call the same tools via MCP (list_tools + call_tool).

FLOW (read this first):
  1. THIS script is the MCP *client*.
  2. It starts mcp_server.py as a *subprocess* (stdio pipes — no URL).
  3. Client asks: list_tools / call_tool  →  JSON-RPC over stdin/stdout.
  4. Server runs the real Python in tools.py and replies.
  5. Script exits → subprocess dies.

  Do NOT run mcp_server.py alone and type into it.
  Run:  python lessons/06_mcp.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "mcp_server.py"
SEP = "=" * 60


def banner(title: str) -> None:
    print(f"\n{SEP}\n{title}\n{SEP}")


async def main() -> None:
    banner("1) CLIENT starts SERVER as subprocess (stdio, no HTTP URL)")
    print(f"command: {sys.executable} {SERVER}")
    print("pipes:   client stdin/stdout  ↔  server stdout/stdin")

    # How to launch the server process. No port — just pipes.
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER)],
        cwd=str(ROOT),
    )

    # Opens the subprocess and gives us read/write streams to it.
    async with stdio_client(params) as (read, write):
        # Session = MCP conversation on those streams.
        async with ClientSession(read, write) as session:
            banner("2) handshake — session.initialize()")
            await session.initialize()
            print("ok — server is ready")

            banner("3) list_tools — 'what can you do?'")
            tools = await session.list_tools()
            for t in tools.tools:
                print(f"  - {t.name}: {t.description}")

            banner("4) list_resources — 'what resources do you have?'")
            resources = await session.list_resources()
            [print(r) for r in resources.resources]
            banner("5) list_prompts — 'what prompts do you have?'")
            prompts = await session.list_prompts()
            [print(p) for p in prompts.prompts]

        

            banner("6) read_resource — 'what is the resource content?'")
            overview = await session.read_resource("lesson://resources")
            print(overview)

            resource1 = await session.read_resource("lesson://resources/resource_1")
            print(resource1) 

            banner("7) read_prompt — 'what is the prompt content?'")
            # prompt = await session.read_prompt("lesson://resources")
            # print(prompt)

            banner("8) call_tool — client asks, server runs tools.py")
            ws = await session.call_tool(
                "word_stats_tool",
                {"text": "hello via MCP"},
            )
            print("word_stats_tool ->", ws.content)

            calc = await session.call_tool(
                "calculator_tool",
                {"expression": "2 + 3 * 4"},
            )
            print("calculator_tool ->", calc.content)

            rev = await session.call_tool(
                "reverse_string_tool",
                {"string": "hello"},
            )
            print("reverse_string_tool ->", rev.content)

    banner("5) done — client exit closes pipes; server process exits")
    print("Same functions as lesson 04, but reached through MCP instead of import.")


if __name__ == "__main__":
    asyncio.run(main())

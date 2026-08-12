"""12 — Same agent task: raw loop vs LangChain sugar.

Frameworks sit on top of messages + tool_calls + the loop you built in 09.
This lesson runs one task both ways so the mapping is obvious.

Both halves honor LLM_PROVIDER (openrouter | anthropic) from .env —
same switch as common.chat — so the LangChain path is not OpenRouter-only.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain.agents import AgentExecutor, create_tool_calling_agent  # pyright: ignore[reportMissingImports]
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  # pyright: ignore[reportMissingImports]
from langchain_core.tools import StructuredTool  # pyright: ignore[reportMissingImports]

from agent import run_agent, tools_used
from common import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    API_KEY,
    LLM_PROVIDER,
    MODEL_TOOLS,
    URL,
    require_api_key,
)
from tools import calculator, word_stats

TASK = (
    "Use calculator for (10 + 5) * 2, then word_stats on 'framework sugar', "
    "then report both briefly."
)


def make_llm(*, temperature: float = 0.1):
    # LangChain needs its own model object (not common.chat).
    if LLM_PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic  # pyright: ignore[reportMissingImports]

        return ChatAnthropic(
            model=ANTHROPIC_MODEL, api_key=ANTHROPIC_API_KEY, temperature=temperature
        )
    from langchain_openai import ChatOpenAI  # pyright: ignore[reportMissingImports]

    return ChatOpenAI(
        model=MODEL_TOOLS,
        api_key=API_KEY,
        base_url=URL.replace("/chat/completions", ""),
        temperature=temperature,
    )


def run_raw() -> None:
    print("=" * 60)
    print("RAW agent.py (lesson 09 loop)")
    print("=" * 60)

    def on_step(event: dict) -> None:
        if event.get("type") == "tool":
            print(f"  tool {event['tool']}({event['arguments']}) -> {event['result']}")

    result = run_agent(TASK, max_steps=6, on_step=on_step)
    print("tools_used:", tools_used(result["steps"]))
    print("final:", result["final"])


def run_langchain() -> None:
    print("\n" + "=" * 60)
    print("LANGCHAIN AgentExecutor (same tools + task)")
    print("=" * 60)

    llm = make_llm()
    lc_tools = [
        StructuredTool.from_function(
            func=word_stats,
            name="word_stats",
            description="Count words, characters, and lines in a text string.",
        ),
        StructuredTool.from_function(
            func=calculator,
            name="calculator",
            description="Evaluate a simple arithmetic expression like '2 + 2 * 3'.",
        ),
    ]
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Solve the task. Use tools when helpful. Be brief."),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
    agent = create_tool_calling_agent(llm, lc_tools, prompt)
    executor = AgentExecutor(agent=agent, tools=lc_tools, verbose=True, max_iterations=6)
    out = executor.invoke({"input": TASK})
    final = out.get("output")
    # ChatAnthropic sometimes returns content blocks instead of a plain string
    if isinstance(final, list):
        final = "\n".join(
            b.get("text", "") for b in final if isinstance(b, dict) and b.get("text")
        ) or final
    print("final:", final)


def print_mapping() -> None:
    print("\n" + "=" * 60)
    print("What maps to what")
    print("=" * 60)
    if LLM_PROVIDER == "anthropic":
        print(f"provider: anthropic  model: {ANTHROPIC_MODEL}")
    else:
        print(f"provider: openrouter  model: {MODEL_TOOLS}")
    print(
        """
| You built              | LangChain piece              |
|------------------------|------------------------------|
| tools.py functions     | StructuredTool / @tool       |
| TOOL_SPECS JSON        | tool schemas (auto)          |
| chat(..., tools=...)   | ChatOpenAI / ChatAnthropic   |
| agent.py while-loop    | AgentExecutor                |
| messages list          | prompt + scratchpad          |
| evals you wrote        | still yours (or Promptfoo)   |

Framework owns: plumbing, retries UI, prompt assembly.
You still own: tools, task design, evals, when to call the model.
"""
    )


def main() -> None:
    require_api_key()
    print_mapping()
    run_raw()
    run_langchain()


if __name__ == "__main__":
    main()

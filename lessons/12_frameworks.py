"""12 — Same agent task: raw loop vs LangChain sugar.

Frameworks sit on top of messages + tool_calls + the loop you built in 09.
This lesson runs one task both ways so the mapping is obvious.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI

from agent import run_agent, tools_used
from common import API_KEY, MODEL_TOOLS, URL, require_api_key
from tools import calculator, word_stats

TASK = (
    "Use calculator for (10 + 5) * 2, then word_stats on 'framework sugar', "
    "then report both briefly."
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

    llm = ChatOpenAI(
        model=MODEL_TOOLS,
        api_key=API_KEY,
        base_url=URL.replace("/chat/completions", ""),
        temperature=0.1,
    )
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
    print("final:", out.get("output"))


def print_mapping() -> None:
    print("\n" + "=" * 60)
    print("What maps to what")
    print("=" * 60)
    print(
        """
| You built              | LangChain piece              |
|------------------------|------------------------------|
| tools.py functions     | StructuredTool / @tool       |
| TOOL_SPECS JSON        | tool schemas (auto)          |
| chat(..., tools=...)   | ChatOpenAI.bind_tools / agent|
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

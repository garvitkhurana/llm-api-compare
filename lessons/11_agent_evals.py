"""11 — Tiny agent eval harness (trajectory + outcome).

FLOW:
  1. Load cases from evals/agent_cases.jsonl
  2. For each: run_agent(task)  →  {final, steps, step_count}
  3. Score expect checks (tools used, substring, max LLM rounds, …)
  4. Scoreboard

  Unlike lesson 10 (text-only), this judges *behavior* + answer.
  Note: each case = several LLM calls — eats free-tier quota fast.

  Run:  python lessons/11_agent_evals.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent import run_agent, tools_used
from common import ANTHROPIC_MODEL, LLM_PROVIDER, MODEL_TOOLS, ROOT, pretty

CASES = ROOT / "evals" / "agent_cases.jsonl"
SEP = "=" * 60


def banner(title: str) -> None:
    print(f"\n{SEP}\n{title}\n{SEP}", flush=True)


def score_case(case: dict, result: dict) -> list[tuple[str, bool]]:
    used = tools_used(result["steps"])
    expect = case["expect"]
    checks: list[tuple[str, bool]] = []

    if "success_substring" in expect:
        ok = expect["success_substring"].lower() in (result["final"] or "").lower()
        checks.append(("success_substring", ok))

    if "tools_used_subset" in expect:
        required = set(expect["tools_used_subset"])
        ok = required.issubset(set(used))
        checks.append(("tools_used_subset", ok))

    if "max_steps" in expect:
        ok = result["step_count"] <= int(expect["max_steps"])
        checks.append(("max_steps", ok))

    if "forbidden_tools" in expect:
        bad = set(expect["forbidden_tools"]) & set(used)
        checks.append(("forbidden_tools", len(bad) == 0))

    return checks


def main() -> None:
    banner("1) SETUP")
    if LLM_PROVIDER == "anthropic":
        print(f"provider: anthropic  model: {ANTHROPIC_MODEL}")
    else:
        print(f"provider: openrouter  model: {MODEL_TOOLS}")
    print(f"cases: {CASES}")
    print("each case burns multiple LLM rounds — watch free-tier limits")

    rows = []
    case_i = 0
    for line in CASES.read_text().splitlines():
        if not line.strip():
            continue
        case_i += 1
        case = json.loads(line)
        cid = case["id"]

        banner(f"2) CASE {case_i} — `{cid}`")
        print("task:", case["task"])
        print("expect:", pretty(case["expect"]))

        banner(f"3) CASE {case_i} — run_agent")
        try:
            result = run_agent(
                case["task"],
                max_steps=case.get("max_steps", 5),
                system=case.get(
                    "system",
                    "Solve the task. Use tools when helpful. Be brief.",
                ),
            )
        except Exception as e:  # noqa: BLE001
            print(f"ERROR: {e}", flush=True)
            rows.append((cid, False, [], {"final": "", "error": str(e)}, []))
            # Daily quota: no point running remaining cases
            if "free-models-per-day" in str(e).lower() or "quota exhausted" in str(e).lower():
                print("stopping remaining cases (quota).", flush=True)
                break
            continue

        used = tools_used(result["steps"])
        print(f"tools_used: {used}")
        print(f"step_count (LLM rounds): {result['step_count']}")
        print(f"final: {(result['final'] or '')[:200]!r}")

        banner(f"4) CASE {case_i} — score expect")
        checks = score_case(case, result)
        for name, ok in checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        passed = bool(checks) and all(ok for _, ok in checks)
        print(f"case `{cid}` overall: {'PASS' if passed else 'FAIL'}")
        rows.append((cid, passed, used, result, checks))

    banner("5) SCOREBOARD")
    print(f"{'id':20} {'pass':5} tools")
    for cid, passed, used, result, checks in rows:
        print(f"{cid:20} {str(passed):5} {used}")
        if checks:
            print(f"  checks: {checks}")
        print(f"  final: {(result.get('final') or '')[:120].replace(chr(10), ' ')}")
        if result.get("error"):
            print(f"  error: {result['error'][:200]}")

    n = len(rows)
    p = sum(1 for _, ok, _, _, _ in rows if ok)
    print(f"\n{p}/{n} passed", flush=True)


if __name__ == "__main__":
    main()

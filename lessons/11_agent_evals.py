"""11 — Tiny agent eval harness (trajectory + outcome)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent import run_agent, tools_used
from common import ROOT

CASES = ROOT / "evals" / "agent_cases.jsonl"


def main() -> None:
    rows = []
    for line in CASES.read_text().splitlines():
        if not line.strip():
            continue
        case = json.loads(line)
        result = run_agent(
            case["task"],
            max_steps=case.get("max_steps", 5),
            system=case.get(
                "system",
                "Solve the task. Use tools when helpful. Be brief.",
            ),
        )
        used = tools_used(result["steps"])
        expect = case["expect"]
        checks = []

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

        passed = all(ok for _, ok in checks)
        rows.append((case["id"], passed, used, result, checks))

    print(f"{'id':20} {'pass':5} tools")
    for cid, passed, used, result, checks in rows:
        print(f"{cid:20} {str(passed):5} {used}")
        print(f"  checks: {checks}")
        print(f"  final: {(result['final'] or '')[:120].replace(chr(10), ' ')}")
        if result.get("error"):
            print(f"  error: {result['error']}")

    n = len(rows)
    p = sum(1 for _, ok, _, _, _ in rows if ok)
    print(f"\n{p}/{n} passed")


if __name__ == "__main__":
    main()

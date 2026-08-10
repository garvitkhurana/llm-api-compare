"""10 — Tiny generation eval harness."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import MODEL_CHAT, ROOT, chat, choice_text

CASES = ROOT / "evals" / "gen_cases.jsonl"


def run_checks(text: str, checks: list[dict]) -> list[tuple[str, bool, str]]:
    out = []
    for c in checks:
        t = c["type"]
        if t == "contains":
            ok = c["value"].lower() in text.lower()
            out.append((t, ok, c["value"]))
        elif t == "not_contains":
            ok = c["value"].lower() not in text.lower()
            out.append((t, ok, c["value"]))
        elif t == "max_chars":
            ok = len(text) <= int(c["value"])
            out.append((t, ok, str(c["value"])))
        else:
            out.append((t, False, "unknown check"))
    return out


def main() -> None:
    rows = []
    for line in CASES.read_text().splitlines():
        if not line.strip():
            continue
        case = json.loads(line)
        data = chat(
            case["messages"],
            model=MODEL_CHAT,
            temperature=0,
            max_tokens=case.get("max_tokens", 200),
        )
        text = choice_text(data)
        results = run_checks(text, case["checks"])
        passed = all(ok for _, ok, _ in results)
        rows.append((case["id"], passed, text, results))

    print(f"{'id':20} {'pass':5} detail")
    for cid, passed, text, results in rows:
        detail = ", ".join(f"{t}={'Y' if ok else 'N'}" for t, ok, _ in results)
        print(f"{cid:20} {str(passed):5} {detail}")
        print(f"  preview: {text[:100].replace(chr(10), ' ')}")

    n = len(rows)
    p = sum(1 for _, ok, _, _ in rows if ok)
    print(f"\n{p}/{n} passed")


if __name__ == "__main__":
    main()

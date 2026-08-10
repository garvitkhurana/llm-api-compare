"""03 — Chat roles + baseline vs constrained generation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import MODEL_CHAT, chat, choice_text, finish_reason, usage

PROMPT = "Python code to give a sqrt of pi to 6 decimal places."
SYSTEM = "Be terse. Output only what was asked. No greetings or extras."
STOP = ["**Output", "Output:", "Here are", "Sure,"]


def main() -> None:
    base = chat(
        [{"role": "user", "content": PROMPT}],
        model=MODEL_CHAT,
        temperature=0.7,
        max_tokens=800,
    )
    cons = chat(
        [
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": PROMPT
                + "\nReply with only the Python code. No markdown fences, no explanation.",
            },
        ],
        model=MODEL_CHAT,
        stop=STOP,
        temperature=0.2,
        max_tokens=400,
    )

    rows = [
        ("baseline", base),
        ("constrained", cons),
    ]
    print(f"{'run':12} {'finish':8} {'chars':6} {'completion_tokens'}")
    for name, data in rows:
        text = choice_text(data)
        u = usage(data) or {}
        print(
            f"{name:12} {str(finish_reason(data)):8} {len(text):6} "
            f"{u.get('completion_tokens')}"
        )

    print("\n=== BASELINE ===\n", choice_text(base))
    print("\n=== CONSTRAINED ===\n", choice_text(cons))


if __name__ == "__main__":
    main()

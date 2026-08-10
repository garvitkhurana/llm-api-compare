"""02 — Multi-turn messages (history)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import MODEL_CHAT, chat, choice_text, finish_reason


def main() -> None:
    messages = [
        {"role": "user", "content": "My favorite number is 17. Remember it."},
        {
            "role": "assistant",
            "content": "Got it — your favorite number is 17.",
        },
        {"role": "user", "content": "What is my favorite number? Reply with only the number."},
    ]
    data = chat(messages, model=MODEL_CHAT, temperature=0, max_tokens=32)
    print("finish_reason:", finish_reason(data))
    print("reply:", choice_text(data))


if __name__ == "__main__":
    main()

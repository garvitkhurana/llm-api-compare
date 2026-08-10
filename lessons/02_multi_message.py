"""02 — Multi-turn messages (history)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import MODEL_CHAT, chat, choice_text, finish_reason


def main() -> None:
    messages = [
        {"role": "user", "content": "Give me a secret code word."},
        {
            "role": "assistant",
            "content": "Secret code: GK.",  # only place code appears
        },
        {
            "role": "user",
            "content": "What secret code did you just give me? Reply with only the code.",
        },
    ]
    data = chat(messages, model=MODEL_CHAT, temperature=0, max_tokens=128)
    print("finish_reason:", finish_reason(data))
    print("reply:", choice_text(data))
    print("---")
    print(data)


if __name__ == "__main__":
    main()

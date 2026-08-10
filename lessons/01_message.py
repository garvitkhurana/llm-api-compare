"""01 — Single user message completion."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import MODEL_CHAT, chat, choice_text, finish_reason, print_usage


def main() -> None:
    data = chat(
        [{"role": "user", "content": "In one sentence, what is a REST API?"}],
        model=MODEL_CHAT,
        max_tokens=120,
    )
    print("finish_reason:", finish_reason(data))
    print_usage(data)
    print("---")
    print(choice_text(data))
    print("---")
    print(data)


if __name__ == "__main__":
    main()

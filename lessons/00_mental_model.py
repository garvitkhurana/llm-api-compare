"""00 — Mental model: one request, look at the shape of the response."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import MODEL_CHAT, chat, finish_reason, pretty, print_usage


def main() -> None:
    data = chat(
        [{"role": "user", "content": "Reply with exactly: pong"}],
        model=MODEL_CHAT,
        temperature=0,
        max_tokens=64,
    )
    print("model:", data.get("model") or MODEL_CHAT)
    print("finish_reason:", finish_reason(data))
    print_usage(data)
    print("message:", pretty(data["choices"][0]["message"]))
    print(
        "\nnote: completion_tokens is the output bill bucket; "
        "thinking can sit inside it (reasoning_tokens)."
    )


if __name__ == "__main__":
    main()

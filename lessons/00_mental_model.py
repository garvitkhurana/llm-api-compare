"""00 — Mental model: one request, look at the shape of the response."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import MODEL_CHAT, chat, finish_reason, pretty, usage


def main() -> None:
    data = chat(
        [{"role": "user", "content": "Reply with exactly: pong"}],
        model=MODEL_CHAT,
        temperature=0,
        max_tokens=32,
    )
    print("model:", data.get("model") or MODEL_CHAT)
    print("finish_reason:", finish_reason(data))
    print("usage:", pretty(usage(data)))
    print("message:", pretty(data["choices"][0]["message"]))


if __name__ == "__main__":
    main()

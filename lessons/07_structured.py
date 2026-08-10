"""07 — JSON output + pydantic validation."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import BaseModel, ValidationError

from common import MODEL_CHAT, chat, choice_text


class CodeAnswer(BaseModel):
    language: str
    code: str


def extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return json.loads(text)


def main() -> None:
    data = chat(
        [
            {
                "role": "system",
                "content": "Respond with JSON only: {\"language\": string, \"code\": string}",
            },
            {
                "role": "user",
                "content": "Python one-liner that prints hello.",
            },
        ],
        model=MODEL_CHAT,
        temperature=0,
        max_tokens=200,
    )
    raw = choice_text(data)
    print("raw:\n", raw)
    try:
        obj = CodeAnswer.model_validate(extract_json(raw))
        print("\nvalidated:", obj.model_dump())
    except (json.JSONDecodeError, ValidationError) as e:
        print("\nVALIDATION FAILED:", e)


if __name__ == "__main__":
    main()

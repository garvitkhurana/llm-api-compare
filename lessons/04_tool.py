"""04 — A tool is just a Python function."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import pretty
from tools import calculator, word_stats


def main() -> None:
    sample = "hello world\nfrom lesson 04"
    print("word_stats:", pretty(word_stats(sample)))
    print("calculator:", pretty(calculator("2 + 3 * 4")))


if __name__ == "__main__":
    main()

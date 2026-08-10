"""04 — A tool is just a Python function."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import pretty
from tools import calculator, word_stats, list_tools, reverse_string


def main() -> None:
    print("list_tools:", pretty(list_tools()))
    sample = "hello world\nfrom lesson 04"
    print("word_stats:", pretty(word_stats(sample)))
    print("calculator:", pretty(calculator("2 + 3 * 4")))
    print("reverse_string:", pretty(reverse_string("hello world")))


if __name__ == "__main__":
    main()

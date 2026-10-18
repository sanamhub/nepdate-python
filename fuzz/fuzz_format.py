"""Fuzz ``NepaliDate.format`` and ``__format__`` with arbitrary patterns (P9-02)."""

from __future__ import annotations

from _common import decode, run

from nepdate import Lang, NepaliDate

_DATE = NepaliDate(2081, 4, 15)


def test_one_input(data: bytes) -> None:
    """Format a valid date with the decoded pattern; any exception is a finding."""
    pattern = decode(data)
    for lang in (Lang.EN, Lang.NE):
        _DATE.format(pattern, lang)
    format(_DATE, pattern)


if __name__ == "__main__":
    run(test_one_input)

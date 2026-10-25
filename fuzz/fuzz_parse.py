"""Fuzz ``NepaliDate.parse`` with arbitrary bytes."""

from __future__ import annotations

import contextlib

from _common import decode, run

from nepdate import NepaliDate
from nepdate._errors import NepDateError


def test_one_input(data: bytes) -> None:
    """Parse the decoded bytes; only ``NepDateError`` is an allowed failure."""
    with contextlib.suppress(NepDateError):
        NepaliDate.parse(decode(data))


if __name__ == "__main__":
    run(test_one_input)

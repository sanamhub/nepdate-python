"""Shared decoding and atheris setup for the three fuzz targets (P9-02)."""

from __future__ import annotations

import sys
from collections.abc import Callable

import atheris

with atheris.instrument_imports():
    from nepdate import Lang, NepaliDate  # noqa: F401
    from nepdate._errors import NepDateError  # noqa: F401


def decode(data: bytes) -> str:
    """Turn arbitrary bytes into text, keeping invalid bytes as lone surrogates.

    Args:
        data: The bytes atheris supplies.

    Returns:
        A string with one code point per byte when the input is not UTF-8.
    """
    return data.decode("utf-8", "surrogateescape")


def run(test_one_input: Callable[[bytes], None]) -> None:
    """Start atheris with the given entry point.

    Args:
        test_one_input: The function atheris calls for every input.
    """
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()

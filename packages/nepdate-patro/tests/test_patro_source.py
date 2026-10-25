"""Source rules for the patro package."""

from __future__ import annotations

import unicodedata
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
_PRIVATE_PREFIX = "nepdate." + "_"


def _sources() -> dict[str, str]:
    """Return every patro source file keyed by its name."""
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(_SRC.rglob("*.py"))}


def _has_private_core_import(source: str) -> bool:
    """Return whether ``source`` imports from a private core module."""
    return _PRIVATE_PREFIX in source


def _invisible(source: str) -> list[str]:
    """Return the code points of raw invisible characters in ``source``."""
    return sorted(
        {
            f"U+{ord(char):04X}"
            for char in source
            if unicodedata.category(char) in ("Cf", "Cc") and char not in "\n\r\t"
        }
    )


def test_patro_uses_only_the_public_core_api() -> None:
    """The patro source imports no private core module."""
    for name, source in _sources().items():
        assert not _has_private_core_import(source), name


def test_private_import_check_negative_control() -> None:
    """The private import check flags a private core import."""
    assert _has_private_core_import("from " + _PRIVATE_PREFIX + "date import NepaliDate\n")
    assert not _has_private_core_import("from nepdate import NepaliDate\n")


def test_no_raw_invisible_characters() -> None:
    """Source files use escapes, not raw format or control characters."""
    for name, source in _sources().items():
        assert not _invisible(source), name


def test_invisible_check_negative_control() -> None:
    """The invisible check names a raw joiner."""
    assert _invisible("a\u200cb") == ["U+200C"]
    assert not _invisible("plain text\n")

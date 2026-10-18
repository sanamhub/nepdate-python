"""Tests and negative controls for the public API snapshot (P9-03)."""

from __future__ import annotations

from typing import Any

_DOC_HEADER = "```python\nclass NepaliDate:\n"
_DOC_FOOTER = "```\n"


def _snapshot(**items: Any) -> dict[str, Any]:
    """Build a minimal snapshot with the given items."""
    return {"schema": 1, "items": items}


def _method(signature: str) -> dict[str, object]:
    """Build a method item."""
    return {"kind": "method", "signature": signature}


def _docs(body: str) -> str:
    """Wrap API declarations in a fenced code block."""
    return _DOC_HEADER + body + _DOC_FOOTER


def test_rename_fails(api_snapshot: Any) -> None:
    """A removed method is reported even when its replacement is documented."""
    old = _snapshot(**{"nepdate.NepaliDate.format": _method("(self, pattern: str) -> str")})
    new = _snapshot(**{"nepdate.NepaliDate.render": _method("(self, pattern: str) -> str")})
    docs = _docs("    def render(self, pattern: str) -> str: ...\n")
    problems = api_snapshot.compare(old, new, docs)
    assert any("removed: nepdate.NepaliDate.format" in problem for problem in problems)


def test_signature_change_fails(api_snapshot: Any) -> None:
    """A changed signature is reported as a changed item."""
    old = _snapshot(**{"nepdate.NepaliDate.format": _method("(self, pattern: str) -> str")})
    new = _snapshot(**{"nepdate.NepaliDate.format": _method("(self, pattern: bytes) -> str")})
    problems = api_snapshot.compare(old, new, "")
    assert problems == ["changed: nepdate.NepaliDate.format"]


def test_undocumented_addition_fails(api_snapshot: Any) -> None:
    """An added method with no declaration in docs/API.md is reported."""
    old = _snapshot()
    new = _snapshot(**{"nepdate.NepaliDate.render": _method("(self) -> str")})
    problems = api_snapshot.compare(old, new, _docs(""))
    assert any(
        "undocumented addition: nepdate.NepaliDate.render" in problem for problem in problems
    )


def test_name_in_prose_only_fails(api_snapshot: Any) -> None:
    """A name mentioned in prose is not a declaration."""
    old = _snapshot()
    new = _snapshot(**{"nepdate.NepaliDate.render": _method("(self) -> str")})
    problems = api_snapshot.compare(old, new, "The method render is described here.\n")
    assert any("undocumented addition" in problem for problem in problems)


def test_documented_addition_passes(api_snapshot: Any) -> None:
    """An added method with an exact declaration is accepted."""
    old = _snapshot()
    new = _snapshot(**{"nepdate.NepaliDate.render": _method("(self, pattern: str) -> str")})
    docs = _docs("    def render(self, pattern: str) -> str: ...\n")
    assert api_snapshot.compare(old, new, docs) == []


def test_changed_exception_base_fails(api_snapshot: Any) -> None:
    """A change to an exception base is a changed item."""
    old = _snapshot(**{"nepdate.NepDateError": {"kind": "exception", "bases": ["ValueError"]}})
    new = _snapshot(**{"nepdate.NepDateError": {"kind": "exception", "bases": ["Exception"]}})
    problems = api_snapshot.compare(old, new, "")
    assert problems == ["changed: nepdate.NepDateError"]


def test_committed_snapshot_matches(api_snapshot: Any) -> None:
    """The committed snapshot matches the installed public surface."""
    assert api_snapshot.check() == []


def test_snapshot_is_stable_and_sorted(api_snapshot: Any) -> None:
    """Two generations serialise identically and the item keys are sorted."""
    first = api_snapshot.surface()
    second = api_snapshot.surface()
    assert api_snapshot.dump(first) == api_snapshot.dump(second)
    assert list(first["items"]) == sorted(first["items"])

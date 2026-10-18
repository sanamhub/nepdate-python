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


_FORMAT = "(self, pattern: str) -> str"
_FORMAT_DOC = "    def format(self, pattern: str) -> str: ...\n"
_RENDER_DOC = "    def render(self, pattern: str) -> str: ...\n"


def test_unchanged_documented_surface_passes(api_snapshot: Any) -> None:
    """An identical, fully declared surface has no problems."""
    snap = _snapshot(**{"nepdate.NepaliDate.format": _method(_FORMAT)})
    assert api_snapshot.compare(snap, snap, _docs(_FORMAT_DOC)) == []


def test_rename_fails(api_snapshot: Any) -> None:
    """A removed method is reported even when its replacement is documented."""
    old = _snapshot(**{"nepdate.NepaliDate.format": _method(_FORMAT)})
    new = _snapshot(**{"nepdate.NepaliDate.render": _method(_FORMAT)})
    problems = api_snapshot.compare(old, new, _docs(_RENDER_DOC))
    assert "removed: nepdate.NepaliDate.format" in problems


def test_signature_change_fails(api_snapshot: Any) -> None:
    """A changed signature is reported as a changed item."""
    old = _snapshot(**{"nepdate.NepaliDate.format": _method(_FORMAT)})
    new = _snapshot(**{"nepdate.NepaliDate.format": _method("(self, pattern: bytes) -> str")})
    docs = _docs("    def format(self, pattern: bytes) -> str: ...\n")
    assert api_snapshot.compare(old, new, docs) == ["changed: nepdate.NepaliDate.format"]


def test_undocumented_addition_fails(api_snapshot: Any) -> None:
    """An added method with no declaration fails twice: not in snapshot and not declared."""
    old = _snapshot()
    new = _snapshot(**{"nepdate.NepaliDate.render": _method("(self) -> str")})
    problems = api_snapshot.compare(old, new, _docs(""))
    assert any("not in snapshot" in problem for problem in problems)
    assert "docs: nepdate.NepaliDate.render is not declared" in problems


def test_name_in_prose_only_fails(api_snapshot: Any) -> None:
    """A name mentioned in prose is not a declaration."""
    snap = _snapshot(**{"nepdate.NepaliDate.render": _method("(self) -> str")})
    problems = api_snapshot.compare(snap, snap, "The method render is described here.\n")
    assert problems == ["docs: nepdate.NepaliDate.render is not declared"]


def test_documented_addition_without_rewrite_fails(api_snapshot: Any) -> None:
    """A declared addition still fails until the snapshot is rewritten."""
    old = _snapshot()
    new = _snapshot(**{"nepdate.NepaliDate.render": _method(_FORMAT)})
    problems = api_snapshot.compare(old, new, _docs(_RENDER_DOC))
    assert problems == [
        "added, not in snapshot (run scripts/api_snapshot.py --write): nepdate.NepaliDate.render"
    ]


def test_documented_addition_after_rewrite_passes(api_snapshot: Any) -> None:
    """Once the snapshot records a declared addition, the check passes."""
    snap = _snapshot(**{"nepdate.NepaliDate.render": _method(_FORMAT)})
    assert api_snapshot.compare(snap, snap, _docs(_RENDER_DOC)) == []


def test_stale_declaration_fails(api_snapshot: Any) -> None:
    """A declaration whose signature no longer matches the surface fails."""
    snap = _snapshot(**{"nepdate.NepaliDate.format": _method(_FORMAT)})
    docs = _docs("    def format(self, pattern: bytes) -> str: ...\n")
    assert api_snapshot.compare(snap, snap, docs) == [
        "docs: nepdate.NepaliDate.format signature differs from the declaration"
    ]


def test_dunder_needs_no_declaration(api_snapshot: Any) -> None:
    """Dunder methods are pinned by the snapshot only."""
    snap = _snapshot(**{"nepdate.NepaliDate.__eq__": _method("(self, other: object) -> bool")})
    assert api_snapshot.compare(snap, snap, _docs("")) == []


def test_all_change_fails(api_snapshot: Any) -> None:
    """A change to a module __all__ is reported."""
    old = {"schema": 1, "all": {"nepdate": ["A"]}, "items": {}}
    new = {"schema": 1, "all": {"nepdate": ["A", "B"]}, "items": {}}
    assert api_snapshot.compare(old, new, "") == ["changed: __all__"]


def test_changed_exception_base_fails(api_snapshot: Any) -> None:
    """A change to an exception base is a changed item."""
    old = _snapshot(**{"nepdate.NepDateError": {"kind": "exception", "bases": ["ValueError"]}})
    new = _snapshot(**{"nepdate.NepDateError": {"kind": "exception", "bases": ["Exception"]}})
    docs = "```python\nclass NepDateError(Exception): ...\n```\n"
    assert api_snapshot.compare(old, new, docs) == ["changed: nepdate.NepDateError"]


def test_committed_snapshot_matches(api_snapshot: Any) -> None:
    """The committed snapshot matches the installed public surface."""
    assert api_snapshot.check() == []


def test_snapshot_is_stable_and_sorted(api_snapshot: Any) -> None:
    """Two generations serialise identically and the item keys are sorted."""
    first = api_snapshot.surface()
    second = api_snapshot.surface()
    assert api_snapshot.dump(first) == api_snapshot.dump(second)
    assert list(first["items"]) == sorted(first["items"])

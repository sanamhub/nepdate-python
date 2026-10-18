"""Unit tests for ``scripts/docs_check.py``."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _doc(root: Path, name: str, text: str) -> Path:
    """Write one documentation file below ``root``.

    Args:
        root: The temporary repository root.
        name: The relative file name.
        text: The file content.

    Returns:
        The written path.
    """
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_clean_docs_pass(docs_check: Any, tmp_path: Path) -> None:
    """A page with a relative link and an absolute link has no problems."""
    _doc(
        tmp_path,
        "README.md",
        "# Read me\n\nSee [the API](docs/API.md) and [PyPI](https://pypi.org/).\n",
    )
    _doc(tmp_path, "docs/API.md", "# API\n")
    assert docs_check.problems(tmp_path) == []


def test_em_dash_is_rejected(docs_check: Any, tmp_path: Path) -> None:
    """The negative control for the em dash rule."""
    _doc(tmp_path, "README.md", "# Read me\n\nA dash \u2014 here.\n")
    assert any("em dash" in problem for problem in docs_check.problems(tmp_path))


def test_task_id_is_rejected(docs_check: Any, tmp_path: Path) -> None:
    """The negative control for the task ID rule."""
    _doc(tmp_path, "CHANGELOG.md", "- Fixed in P4-03.\n")
    assert any("task ID" in problem for problem in docs_check.problems(tmp_path))


def test_broken_relative_link_is_rejected(docs_check: Any, tmp_path: Path) -> None:
    """The negative control for relative link resolution."""
    _doc(tmp_path, "README.md", "See [missing](docs/missing.md).\n")
    assert any("does not resolve" in problem for problem in docs_check.problems(tmp_path))


def test_anchor_and_absolute_links_are_not_files(docs_check: Any, tmp_path: Path) -> None:
    """A fragment and a URL are not resolved as local paths."""
    _doc(tmp_path, "README.md", "[top](#read-me) [hub](https://github.com/sanamhub/nepdate)\n")
    assert docs_check.problems(tmp_path) == []


def test_docs_directory_is_checked(docs_check: Any, tmp_path: Path) -> None:
    """Every top-level page under docs/ is part of the gate."""
    _doc(tmp_path, "README.md", "# Read me\n")
    _doc(tmp_path, "docs/benchmarks.md", "A dash \u2014 here.\n")
    assert any("docs/benchmarks.md" in problem for problem in docs_check.problems(tmp_path))

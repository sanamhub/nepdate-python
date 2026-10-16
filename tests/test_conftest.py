"""Tests for the shared conftest helpers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path


def test_repo_root_holds_version(repo_root: Path) -> None:
    """The repository root fixture points at the directory holding shared/VERSION."""
    assert (repo_root / "shared" / "VERSION").is_file()


def test_repo_root_finds_vectors(repo_root: Path) -> None:
    """Vector files are reachable from the repository root fixture."""
    assert (repo_root / "shared" / "spec" / "vectors" / "parse.tsv").is_file()


def test_read_vectors_tsv(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """A .tsv vector reads with a tab delimiter and the expected columns."""
    rows = vector_reader("parse.tsv")
    assert rows and {"input", "strict", "lenient"} <= rows[0].keys()


def test_read_vectors_csv(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """A .csv vector reads with a comma delimiter."""
    rows = vector_reader("month-boundaries.csv")
    assert rows

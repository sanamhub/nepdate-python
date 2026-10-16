"""Shared fixtures and vector readers for the core test suite."""

from __future__ import annotations

import csv
from collections.abc import Callable
from pathlib import Path

import pytest


def _repo_root() -> Path:
    """Return the repository root by walking up to the directory holding shared/VERSION.

    Returns:
        The repository root directory.

    Raises:
        RuntimeError: No ancestor directory holds ``shared/VERSION``.
    """
    for parent in (Path(__file__).resolve().parent, *Path(__file__).resolve().parents):
        if (parent / "shared" / "VERSION").is_file():
            return parent
    raise RuntimeError("repository root not found: no shared/VERSION above the tests directory")


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Return the repository root directory."""
    return _repo_root()


def vectors_path(*parts: str) -> Path:
    """Resolve a path under ``shared/spec/vectors/`` from the repository root.

    Args:
        parts: Path components below the vectors directory.

    Returns:
        The resolved path, independent of the current working directory.
    """
    return _repo_root().joinpath("shared", "spec", "vectors", *parts)


def read_vectors(*parts: str) -> list[dict[str, str]]:
    """Read a TSV or CSV vector file into a list of row dictionaries.

    Args:
        parts: Path components below the vectors directory.

    Returns:
        One dictionary per data row, keyed by the header row.
    """
    path = vectors_path(*parts)
    delimiter = "\t" if path.suffix == ".tsv" else ","
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


@pytest.fixture(scope="session")
def vector_reader() -> Callable[..., list[dict[str, str]]]:
    """Return the ``read_vectors`` helper so tests use it without importing conftest."""
    return read_vectors

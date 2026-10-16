"""Shared fixtures for the patro test suite."""

from __future__ import annotations

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

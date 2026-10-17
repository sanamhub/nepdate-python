"""Every name in each public surface has a docstring."""

from __future__ import annotations

import inspect

import nepdate
import nepdate_patro


def test_core_public_names_have_docstrings() -> None:
    """Every name in ``nepdate.__all__`` carries a docstring."""
    missing = [name for name in nepdate.__all__ if not inspect.getdoc(getattr(nepdate, name))]
    assert missing == []


def test_patro_public_names_have_docstrings() -> None:
    """Every name in ``nepdate_patro.__all__`` carries a docstring."""
    missing = [
        name for name in nepdate_patro.__all__ if not inspect.getdoc(getattr(nepdate_patro, name))
    ]
    assert missing == []

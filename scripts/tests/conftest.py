"""Fixtures that load ``scripts/`` modules for testing.

``scripts/`` is not a package, so the tests import the files with importlib instead of a regular
import. The fixtures expose the loaded modules by name.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent


def _load(name: str, filename: str) -> Any:
    """Load a Python file from ``scripts/`` as a module.

    Args:
        name: The module name to register.
        filename: The file name inside ``scripts/``.

    Returns:
        The loaded module.

    Raises:
        RuntimeError: The file cannot be loaded as a module.
    """
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {filename} as a module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def codegen() -> Any:
    """Load ``scripts/codegen.py`` as a module."""
    return _load("codegen_script", "codegen.py")


@pytest.fixture(scope="session")
def ci() -> Any:
    """Load ``scripts/ci.py`` as a module."""
    return _load("ci_script", "ci.py")


@pytest.fixture(scope="session")
def docs_check() -> Any:
    """Load ``scripts/docs_check.py`` as a module."""
    return _load("docs_check_script", "docs_check.py")


@pytest.fixture(scope="session")
def benchmark_inputs() -> Any:
    """Load ``benchmarks/inputs.py`` as a module."""
    return _load("benchmark_inputs_script", "../benchmarks/inputs.py")

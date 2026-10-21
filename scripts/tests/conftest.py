"""Fixtures that load ``scripts/`` modules for testing.

``scripts/`` is not a package, so the tests import the files with importlib instead of a regular
import. The fixtures expose the loaded modules by name.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


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
def mutation_check() -> Any:
    """Load ``scripts/mutation_check.py`` as a module."""
    return _load("mutation_check_script", "mutation_check.py")


@pytest.fixture(scope="session")
def api_snapshot() -> Any:
    """Load ``scripts/api_snapshot.py`` as a module."""
    return _load("api_snapshot_script", "api_snapshot.py")


@pytest.fixture(scope="session")
def ci_matrix() -> Any:
    """Load ``scripts/ci_matrix.py`` as a module."""
    return _load("ci_matrix_script", "ci_matrix.py")


@pytest.fixture(scope="session")
def data_status() -> Any:
    """Load ``scripts/data_status.py`` as a module."""
    return _load("data_status_script", "data_status.py")


@pytest.fixture(scope="session")
def verify_published() -> Any:
    """Load ``scripts/verify_published.py`` as a module."""
    return _load("verify_published_script", "verify_published.py")


@pytest.fixture(scope="session")
def versions() -> Any:
    """Load ``scripts/versions.py`` as a module."""
    return _load("versions_script", "versions.py")


@pytest.fixture(scope="session")
def rehearsal() -> Any:
    """Load ``scripts/rehearsal.py`` as a module."""
    return _load("rehearsal_script", "rehearsal.py")


@pytest.fixture(scope="session")
def benchmark_inputs() -> Any:
    """Load ``benchmarks/inputs.py`` as a module."""
    return _load("benchmark_inputs_script", "../benchmarks/inputs.py")


@pytest.fixture(scope="session")
def bench_run() -> Any:
    """Load ``benchmarks/run.py`` as a module."""
    return _load("bench_run_script", "../benchmarks/run.py")

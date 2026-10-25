"""The local CI matrix reads ``ci.yml`` instead of keeping its own version list."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

WORKFLOW = """\
name: ci
on: [pull_request]
jobs:
  test:
    strategy:
      matrix:
        include:
          - { os: ubuntu-latest, python: "3.11" }
          - { os: ubuntu-latest, python: "3.12" }
          - { os: ubuntu-latest, python: "3.11" }
          - { os: ubuntu-latest, python: "3.14t" }
  test-prerelease:
    strategy:
      matrix:
        include:
          - { os: ubuntu-latest, python: "3.15" }
"""


def _workflow(tmp_path: Path, text: str = WORKFLOW) -> Path:
    """Write a workflow file below ``tmp_path``.

    Args:
        tmp_path: The temporary directory.
        text: The workflow contents.

    Returns:
        The workflow path.
    """
    path = tmp_path / "ci.yml"
    path.write_text(text, encoding="utf-8")
    return path


def test_matrix_versions_reads_the_test_job(ci_matrix: Any, tmp_path: Path) -> None:
    """Versions come from the include list, deduplicated, and the 3.15 job is excluded."""
    assert ci_matrix.matrix_versions(_workflow(tmp_path)) == ["3.11", "3.12", "3.14t"]


def test_matrix_versions_change_with_the_workflow(ci_matrix: Any, tmp_path: Path) -> None:
    """A hardcoded list would return the same versions for both files."""
    first = _workflow(tmp_path, WORKFLOW)
    second = tmp_path / "second.yml"
    second.write_text(WORKFLOW.replace('python: "3.12"', 'python: "3.99"'), encoding="utf-8")
    first_versions = ci_matrix.matrix_versions(first)
    second_versions = ci_matrix.matrix_versions(second)
    assert first_versions != second_versions
    assert "3.99" in second_versions
    assert "3.99" not in first_versions


def test_matrix_versions_requires_a_test_job(ci_matrix: Any, tmp_path: Path) -> None:
    """A workflow without the test matrix is an error, not an empty success."""
    path = _workflow(tmp_path, "name: ci\njobs:\n  other:\n    runs-on: ubuntu-latest\n")
    with pytest.raises(ci_matrix.MatrixError):
        ci_matrix.matrix_versions(path)


def test_environment_puts_everything_under_the_cache_root(
    ci_matrix: Any, tmp_path: Path, monkeypatch: Any
) -> None:
    """The project environment, Python installs, uv cache and temp files share one root."""
    monkeypatch.setenv("VIRTUAL_ENV", ".venv")
    env = ci_matrix.environment(tmp_path, "3.14t")
    assert "VIRTUAL_ENV" not in env
    assert env["UV_PROJECT_ENVIRONMENT"] == str(tmp_path / "envs" / "3.14t")
    assert env["UV_PYTHON_INSTALL_DIR"] == str(tmp_path / "python")
    assert env["UV_CACHE_DIR"] == str(tmp_path / "uv-cache")
    assert env["TEMP"] == str(tmp_path / "tmp")
    assert env["TMP"] == str(tmp_path / "tmp")
    assert env["UV_PYTHON"] == "3.14t"


def test_parallel_versions_write_nothing_shared(ci_matrix: Any, tmp_path: Path) -> None:
    """Two versions running at once get separate build, coverage and mypy folders."""
    first = ci_matrix.environment(tmp_path, "3.11")
    second = ci_matrix.environment(tmp_path, "3.14t")
    for key in ("NEPDATE_CI_DIST", "COVERAGE_FILE", "MYPY_CACHE_DIR"):
        assert first[key] != second[key]
        assert Path(first[key]).is_relative_to(tmp_path)
        assert Path(second[key]).is_relative_to(tmp_path)


def test_ci_builds_into_the_folder_the_matrix_gives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """scripts/ci.py reads NEPDATE_CI_DIST, so parallel runs never share dist/."""
    path = Path(__file__).resolve().parent.parent / "ci.py"

    def load() -> Any:
        """Load a fresh copy of scripts/ci.py, which reads the variable at import."""
        spec = importlib.util.spec_from_file_location("ci_dist_probe", path)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    monkeypatch.setenv("NEPDATE_CI_DIST", str(tmp_path / "dist-3.11"))
    assert tmp_path / "dist-3.11" == load().DIST
    monkeypatch.delenv("NEPDATE_CI_DIST")
    module = load()
    assert module.DIST == module.ROOT / "dist"


def test_skip_is_not_a_pass(ci_matrix: Any) -> None:
    """The summary keeps a skipped version out of the passed count."""
    results = [
        ci_matrix.RunResult("3.11", "passed", "ci: 10/10 gates passed"),
        ci_matrix.RunResult("3.14t", "skipped", "uv cannot provide Python 3.14t"),
    ]
    line = ci_matrix.summary_line(results)
    assert "1 passed" in line
    assert "1 skipped" in line
    assert "3.14t" in line
    assert "2 passed" not in line


def test_a_missing_version_is_skipped(ci_matrix: Any, tmp_path: Path) -> None:
    """A version uv cannot provide is skipped and never counted as passed."""
    result = ci_matrix.run_version("9.99", tmp_path)
    assert result.status == "skipped"
    assert "9.99" in result.detail


def test_more_than_four_jobs_is_rejected(ci_matrix: Any) -> None:
    """The task limit is enforced by the argument parser."""
    with pytest.raises(SystemExit):
        ci_matrix.parse_args(["--jobs", "5"])


def test_list_prints_the_matrix(ci_matrix: Any, tmp_path: Path, capsys: Any) -> None:
    """``--list`` prints one version per line without running a gate."""
    path = _workflow(tmp_path)
    assert ci_matrix.main(["--workflow", str(path), "--list"]) == 0
    assert capsys.readouterr().out.splitlines() == ["3.11", "3.12", "3.14t"]

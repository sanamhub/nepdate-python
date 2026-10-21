"""The post-upload check installs exact versions, retries while the index catches up, and checks."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest


def _done(code: int) -> subprocess.CompletedProcess[str]:
    """Return a finished process with an exit code.

    Args:
        code: The exit code.

    Returns:
        The completed process.
    """
    return subprocess.CompletedProcess([], code, "", "No matching distribution" if code else "")


def test_install_command_pins_both_exact_versions(verify_published: Any) -> None:
    """Both distributions are pinned, nothing comes from a cache."""
    command = verify_published.install_command(Path("py"), "0.1.0b1", "https://x/simple/", "")
    assert command[-2:] == ["nepdate-core==0.1.0b1", "nepdate-patro==0.1.0b1"]
    assert "--no-cache-dir" in command
    assert "--extra-index-url" not in command


def test_install_command_adds_the_extra_index(verify_published: Any) -> None:
    """TestPyPI runs take dependencies from a second index."""
    command = verify_published.install_command(
        Path("py"), "0.1.0b1", "https://test.pypi.org/simple/", "https://pypi.org/simple/"
    )
    assert command[command.index("--extra-index-url") + 1] == "https://pypi.org/simple/"


def test_install_retries_until_the_index_has_the_files(verify_published: Any) -> None:
    """Two misses and a hit install, with a pause between attempts."""
    results = iter([_done(1), _done(1), _done(0)])
    pauses: list[float] = []
    now = iter([0.0, 1.0, 2.0, 3.0, 4.0])
    verify_published.install_with_retries(
        ["pip"], 600, run=lambda _: next(results), sleep=pauses.append, clock=lambda: next(now)
    )
    assert pauses == [verify_published.RETRY_SECONDS, verify_published.RETRY_SECONDS]


def test_install_gives_up_when_the_wait_runs_out(verify_published: Any) -> None:
    """A version that never appears fails with the installer's last lines."""
    now = iter([0.0, 10.0, 700.0])
    with pytest.raises(RuntimeError, match="No matching distribution"):
        verify_published.install_with_retries(
            ["pip"], 600, run=lambda _: _done(1), sleep=lambda _: None, clock=lambda: next(now)
        )


def test_check_output_needs_both_versions(verify_published: Any) -> None:
    """The check program's version line must name the expected version twice."""
    verify_published.check_output("0.1.0b1 0.1.0b1\n", "0.1.0b1")
    with pytest.raises(RuntimeError, match=r"expected 0\.1\.0b1"):
        verify_published.check_output("0.1.0b1 0.0.9\n", "0.1.0b1")


def test_check_program_uses_the_readme_date(verify_published: Any) -> None:
    """The program converts the README date and reads its tithi."""
    assert "NepaliDate(2080, 5, 15)" in verify_published.CHECK
    assert "from nepdate_patro import info" in verify_published.CHECK

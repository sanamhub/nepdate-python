"""The post-upload check installs exact versions, retries while the index catches up, and checks."""

from __future__ import annotations

import json
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


def test_latest_reads_info_version(verify_published: Any) -> None:
    """PyPI's info.version is the version a plain install gets."""
    payload = json.dumps({"info": {"version": "0.4.2"}})
    assert verify_published.parse_latest(payload) == "0.4.2"


def test_latest_keeps_the_pep_440_spelling(verify_published: Any) -> None:
    """A pre-release keeps PyPI's spelling and is not rewritten to semver."""
    payload = json.dumps({"info": {"version": "0.1.0b1"}})
    assert verify_published.parse_latest(payload) == "0.1.0b1"


def test_latest_rejects_a_response_without_a_version(verify_published: Any) -> None:
    """A registry answer without info.version fails instead of installing nothing."""
    with pytest.raises(RuntimeError, match=r"info\.version"):
        verify_published.parse_latest(json.dumps({"info": {}}))


def _release(files: list[dict[str, Any]]) -> str:
    """Return a PyPI JSON body that lists one version with the given files.

    Args:
        files: The release file entries.

    Returns:
        The JSON text.
    """
    return json.dumps({"info": {"version": "0.1.0b1"}, "releases": {"0.1.0b1": files}})


def _files(*names: str, yanked: bool = False) -> list[dict[str, Any]]:
    """Return release file entries for the given file names.

    Args:
        names: The file names under the files host.
        yanked: Whether every entry is yanked.

    Returns:
        The release file entries.
    """
    return [
        {
            "packagetype": "bdist_wheel" if name.endswith(".whl") else "sdist",
            "url": f"https://files.example/{name}",
            "yanked": yanked,
        }
        for name in names
    ]


def test_metadata_heads_the_wheel_and_sdist_of_both_packages(verify_published: Any) -> None:
    """The daily check asks for every file of both distributions and downloads none."""
    payloads = {
        verify_published.package_json(verify_published.CORE_DIST): _release(
            _files("nepdate_core-0.1.0b1-py3-none-any.whl", "nepdate_core-0.1.0b1.tar.gz")
        ),
        verify_published.package_json(verify_published.PATRO_DIST): _release(
            _files("nepdate_patro-0.1.0b1-py3-none-any.whl", "nepdate_patro-0.1.0b1.tar.gz")
        ),
    }
    heads: list[str] = []

    def head(url: str) -> int:
        heads.append(url)
        return 200

    lines = verify_published.check_metadata("0.1.0b1", get=payloads.__getitem__, head=head)
    assert heads == [
        "https://files.example/nepdate_core-0.1.0b1-py3-none-any.whl",
        "https://files.example/nepdate_core-0.1.0b1.tar.gz",
        "https://files.example/nepdate_patro-0.1.0b1-py3-none-any.whl",
        "https://files.example/nepdate_patro-0.1.0b1.tar.gz",
    ]
    assert len(lines) == len(payloads)
    assert "nepdate-core 0.1.0b1 is listed" in lines[0]
    assert "nepdate-patro 0.1.0b1 is listed" in lines[1]


def test_metadata_rejects_a_version_that_is_not_listed(verify_published: Any) -> None:
    """A version missing from releases fails the daily check."""
    with pytest.raises(RuntimeError, match=r"does not list nepdate-core 0\.1\.0b1"):
        verify_published.check_metadata(
            "0.1.0b1", get=lambda _: json.dumps({"releases": {}}), head=lambda _: 200
        )


def test_metadata_rejects_a_yanked_version(verify_published: Any) -> None:
    """A version whose files are all yanked fails the daily check."""
    with pytest.raises(RuntimeError, match="yanked"):
        verify_published.check_metadata(
            "0.1.0b1",
            get=lambda _: _release(_files("nepdate_core-0.1.0b1.tar.gz", yanked=True)),
            head=lambda _: 200,
        )


def test_metadata_rejects_a_file_that_does_not_answer(verify_published: Any) -> None:
    """A file URL that answers 404 fails the daily check before a user finds it."""
    with pytest.raises(RuntimeError, match="answered 404"):
        verify_published.check_metadata(
            "0.1.0b1",
            get=lambda _: _release(_files("nepdate_core-0.1.0b1.tar.gz")),
            head=lambda _: 404,
        )

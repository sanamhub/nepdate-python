"""Install a released version from a package index and use it the way a user would.

``verify-published.yml`` runs this after an upload, on every runner OS and on the oldest and
newest supported Python. It creates a fresh venv outside the checkout, installs both exact
versions (retrying while the index catches up), then runs one conversion and one patro lookup
whose results are fixed data, so a wrong file or a wrong version fails here and not for a user.

    python scripts/verify_published.py 0.1.0b1
    python scripts/verify_published.py 0.1.0b1 --index-url https://test.pypi.org/simple/
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

CORE_DIST = "nepdate-core"
PATRO_DIST = "nepdate-patro"
PYPI = "https://pypi.org/simple/"
RETRY_SECONDS = 30
# The same date as the README quick start. Fixed data: a conversion or table change that moves
# any of these lines fails the check on purpose.
CHECK = """\
import importlib.metadata as metadata
from nepdate import Lang, NepaliDate
from nepdate_patro import info

d = NepaliDate(2080, 5, 15)
assert str(d) == "2080/05/15", str(d)
assert d.to_date().isoformat() == "2023-09-01", d.to_date()
assert d.long(weekday=True, lang=Lang.NE) == "शुक्रवार, भदौ १५, २०८०"
assert NepaliDate.parse("2080/05/15") == d
day = info(d)
assert day.tithi is not None and day.tithi.label(Lang.EN) == "Dwitiya", day.tithi
print(metadata.version("nepdate-core"), metadata.version("nepdate-patro"))
"""

Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command and capture its output as UTF-8 text.

    Args:
        command: The command and its arguments.

    Returns:
        The completed process.
    """
    env = {**os.environ, "PYTHONUTF8": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1"}
    return subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8", check=False, env=env
    )


def _venv_python(venv: Path) -> Path:
    """Return the interpreter inside a venv on this OS.

    Args:
        venv: The venv directory.

    Returns:
        The path of its Python executable.
    """
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def install_command(python: Path, version: str, index_url: str, extra_index_url: str) -> list[str]:
    """Return the pip command that installs both exact versions and nothing cached.

    Args:
        python: The venv interpreter.
        version: The PyPI version, for example ``0.1.0b1``.
        index_url: The index to install from.
        extra_index_url: A second index for dependencies, or an empty string.

    Returns:
        The command line.
    """
    command = [str(python), "-m", "pip", "install", "--no-cache-dir", "--index-url", index_url]
    if extra_index_url:
        command += ["--extra-index-url", extra_index_url]
    return [*command, f"{CORE_DIST}=={version}", f"{PATRO_DIST}=={version}"]


def install_with_retries(
    command: list[str],
    wait_seconds: int,
    run: Runner = _run,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> None:
    """Run the install until it succeeds or the wait runs out.

    A new upload can take minutes to appear in the simple index, so a failed install is retried.

    Args:
        command: The pip command.
        wait_seconds: How long to keep retrying.
        run: The command runner, replaced in tests.
        sleep: The pause between attempts, replaced in tests.
        clock: A monotonic clock, replaced in tests.

    Raises:
        RuntimeError: The install still fails when the wait runs out.
    """
    deadline = clock() + wait_seconds
    while True:
        result = run(command)
        if result.returncode == 0:
            return
        left = deadline - clock()
        if left <= 0:
            tail = "\n".join((result.stdout + result.stderr).strip().splitlines()[-10:])
            raise RuntimeError(f"install failed after {wait_seconds} s:\n{tail}")
        pause = min(RETRY_SECONDS, left)
        print(f"verify: install failed, retrying in {pause:.0f} s", flush=True)
        sleep(pause)


def check_output(output: str, version: str) -> None:
    """Check that the installed distributions report the expected version.

    Args:
        output: The check program's standard output.
        version: The expected PyPI version.

    Raises:
        RuntimeError: The versions differ.
    """
    if output.split() != [version, version]:
        raise RuntimeError(f"installed versions are {output.split()}, expected {version} twice")


def verify(version: str, index_url: str, extra_index_url: str, wait_seconds: int) -> None:
    """Install both distributions into a fresh venv and run the check.

    Args:
        version: The PyPI version, for example ``0.1.0b1``.
        index_url: The index to install from.
        extra_index_url: A second index for dependencies, or an empty string.
        wait_seconds: How long to retry the install.

    Raises:
        RuntimeError: The venv, the install or the check fails.
    """
    with tempfile.TemporaryDirectory(prefix="nepdate-verify-") as tmp:
        venv = Path(tmp) / "venv"
        created = _run([sys.executable, "-m", "venv", str(venv)])
        if created.returncode != 0:
            raise RuntimeError(f"venv failed: {created.stderr.strip()}")
        python = _venv_python(venv)
        command = install_command(python, version, index_url, extra_index_url)
        install_with_retries(command, wait_seconds)
        # Run from the temporary directory so nothing in the checkout can shadow the install.
        result = subprocess.run(
            [str(python), "-c", CHECK],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            cwd=tmp,
            env={**os.environ, "PYTHONUTF8": "1"},
        )
        if result.returncode != 0:
            raise RuntimeError(f"check failed:\n{result.stdout}{result.stderr}")
        check_output(result.stdout, version)
    print(f"verify: {CORE_DIST} and {PATRO_DIST} {version} from {index_url}: ok")


def main(argv: list[str] | None = None) -> int:
    """Parse the arguments and verify one released version.

    Args:
        argv: The command line arguments; ``sys.argv[1:]`` when None.

    Returns:
        0 when the released version installs and works, 1 otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("version", help="the PyPI version, for example 0.1.0b1")
    parser.add_argument("--index-url", default=PYPI)
    parser.add_argument("--extra-index-url", default="")
    parser.add_argument("--wait-seconds", type=int, default=900)
    args = parser.parse_args(argv)
    try:
        verify(args.version, args.index_url, args.extra_index_url, args.wait_seconds)
    except RuntimeError as exc:
        print(f"verify: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

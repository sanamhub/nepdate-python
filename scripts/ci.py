"""Run every quality gate in order and stop at the first failure.

The entry point is ``uv run python scripts/ci.py``. Each gate is defined in ADR-0004. Gates 6 and
7 install the wheels built from this checkout into throwaway virtualenvs and test each
distribution on its own, so a core-only install is proven to have no ``nepdate_patro``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
CORE_DIST = "nepdate"
PATRO_DIST = "nepdate-patro"
PATRO_MODULE = "nepdate_patro"
CORE_PREFIX = "nepdate-"
PATRO_PREFIX = "nepdate_patro-"
EVENT_ANCHOR = "World Day Against Human Trafficking"
CORE_IMPORT_LIMIT_US = 5_000
PATRO_IMPORT_LIMIT_US = 10_000
COVERAGE_MIN = 90
IMPORT_TIME_FIELDS = 3


class GateError(Exception):
    """Raised when a gate fails, carrying a human-readable reason."""


def _run(
    cmd: list[str], *, check: bool = True, capture: bool = False
) -> subprocess.CompletedProcess[str]:
    """Run a command from the repository root and print it first.

    Args:
        cmd: The command and its arguments, no shell involved.
        check: Raise GateError when the command exits non-zero.
        capture: Capture stdout and stderr instead of streaming them.

    Returns:
        The completed process, with stdout and stderr as text.

    Raises:
        GateError: The command exited non-zero and ``check`` is true.
    """
    print("+", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT, capture_output=capture, text=True, check=False)
    if check and result.returncode != 0:
        raise GateError(f"command failed ({result.returncode}): {' '.join(cmd)}")
    return result


def gate_ruff() -> None:
    """Format check and lint the whole repository."""
    _run(["uv", "run", "ruff", "format", "--check"])
    _run(["uv", "run", "ruff", "check"])


def gate_mypy() -> None:
    """Type-check the packages and the scripts."""
    _run(["uv", "run", "mypy", "--strict", "src", "packages/nepdate-patro/src", "scripts"])


def gate_pytest() -> None:
    """Run every test suite and enforce the per-package coverage floor."""
    _run(
        [
            "uv",
            "run",
            "pytest",
            "tests",
            "packages/nepdate-patro/tests",
            "scripts/tests",
            f"--cov={CORE_DIST}",
            f"--cov={PATRO_MODULE}",
            "--cov-report=term",
        ]
    )
    # ADR-0004: each package is measured on its own, not as one combined total.
    _run(
        [
            "uv",
            "run",
            "coverage",
            "report",
            f"--include=*/{CORE_DIST}/*",
            f"--fail-under={COVERAGE_MIN}",
        ]
    )
    _run(
        [
            "uv",
            "run",
            "coverage",
            "report",
            f"--include=*/{PATRO_MODULE}/*",
            f"--fail-under={COVERAGE_MIN}",
        ]
    )


def gate_codegen() -> None:
    """Fail when a generated file drifted from the shared data."""
    _run(["uv", "run", "python", "scripts/codegen.py", "--check"])


def _import_time(statement: str, module: str) -> tuple[int, dict[str, int]]:
    """Measure the best cumulative import time of a module over three runs.

    Args:
        statement: The ``-c`` script that imports the module.
        module: The module whose cumulative import time is read.

    Returns:
        The minimum cumulative microseconds and the parsed times of the best run.

    Raises:
        GateError: The module did not appear in the import-time report.
    """
    best = sys.maxsize
    best_times: dict[str, int] = {}
    for _ in range(3):
        result = _run(["uv", "run", "python", "-X", "importtime", "-c", statement], capture=True)
        times = _parse_importtime(result.stderr)
        if module not in times:
            raise GateError(f"no {module} entry in import-time output")
        if times[module] < best:
            best = times[module]
            best_times = times
    return best, best_times


def _parse_importtime(output: str) -> dict[str, int]:
    """Map module names to cumulative microseconds from ``-X importtime`` output.

    Args:
        output: The stderr of an ``-X importtime`` run.

    Returns:
        Module names keyed to their cumulative microseconds.
    """
    times: dict[str, int] = {}
    for line in output.splitlines():
        if not line.startswith("import time:"):
            continue
        parts = line.split("|")
        if len(parts) != IMPORT_TIME_FIELDS:
            continue
        try:
            cumulative = int(parts[1].strip())
        except ValueError:
            continue
        times[parts[2].strip()] = cumulative
    return times


def gate_import_time() -> None:
    """Check the import budget and that the core never loads the patro."""
    core_us, core_times = _import_time("import nepdate", CORE_DIST)
    if PATRO_MODULE in core_times:
        raise GateError(f"import nepdate loaded {PATRO_MODULE}")
    if core_us >= CORE_IMPORT_LIMIT_US:
        raise GateError(f"import nepdate takes {core_us} us, limit {CORE_IMPORT_LIMIT_US}")
    patro_us, _ = _import_time(f"import nepdate; import {PATRO_MODULE}", PATRO_MODULE)
    if patro_us >= PATRO_IMPORT_LIMIT_US:
        raise GateError(f"import {PATRO_MODULE} takes {patro_us} us, limit {PATRO_IMPORT_LIMIT_US}")


def _find_archive(prefix: str, suffix: str) -> Path:
    """Return the one archive in dist/ with the given prefix and suffix.

    Args:
        prefix: The file name prefix.
        suffix: The file name suffix.

    Returns:
        The matching archive path.

    Raises:
        GateError: There is not exactly one match.
    """
    matches = [p for p in DIST.iterdir() if p.name.startswith(prefix) and p.name.endswith(suffix)]
    if len(matches) != 1:
        raise GateError(f"expected one {prefix}*{suffix} in {DIST}, found {len(matches)}")
    return matches[0]


def _wheel_metadata(wheel: Path) -> str:
    """Read the METADATA file from a wheel.

    Args:
        wheel: The wheel path.

    Returns:
        The METADATA contents.

    Raises:
        GateError: The wheel has no METADATA.
    """
    with zipfile.ZipFile(wheel) as archive:
        for name in archive.namelist():
            if name.endswith(".dist-info/METADATA"):
                return archive.read(name).decode("utf-8")
    raise GateError(f"no METADATA in {wheel}")


def _metadata_version(metadata: str) -> str:
    """Read the ``Version`` field from wheel METADATA.

    Args:
        metadata: The METADATA contents.

    Returns:
        The version string.

    Raises:
        GateError: The METADATA has no Version field.
    """
    for line in metadata.splitlines():
        if line.startswith("Version:"):
            return line.split(":", 1)[1].strip()
    raise GateError("no Version field in METADATA")


def _archive_contains(path: Path, needle: str) -> bool:
    """Return whether any file inside a wheel or sdist contains the needle.

    Uses zipfile and tarfile only, so it works on Windows without external tools.

    Args:
        path: A ``.whl`` or ``.tar.gz`` archive.
        needle: The text to look for.

    Returns:
        True when at least one member contains the needle bytes.
    """
    needle_bytes = needle.encode("utf-8")
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            return any(needle_bytes in archive.read(name) for name in archive.namelist())
    with tarfile.open(path, "r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            extracted = archive.extractfile(member)
            if extracted is not None and needle_bytes in extracted.read():
                return True
    return False


def _venv_python(venv: Path) -> Path:
    """Return the Python executable inside a virtualenv.

    Args:
        venv: The virtualenv directory.

    Returns:
        The interpreter path for this platform.
    """
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def gate_core_alone() -> None:
    """Build both distributions and prove the core wheel has no patro content."""
    shutil.rmtree(DIST, ignore_errors=True)
    _run(["uv", "build", "--all-packages"])
    core_wheel = _find_archive(CORE_PREFIX, ".whl")
    core_sdist = _find_archive(CORE_PREFIX, ".tar.gz")

    metadata = _wheel_metadata(core_wheel)
    for line in metadata.splitlines():
        if line.startswith("Requires-Dist:") and PATRO_DIST in line:
            raise GateError(f"core wheel depends on {PATRO_DIST}: {line}")
    for archive in (core_wheel, core_sdist):
        if _archive_contains(archive, EVENT_ANCHOR):
            raise GateError(f"{archive.name} contains patro data")

    with tempfile.TemporaryDirectory() as tmp:
        venv = Path(tmp) / "venv"
        _run(["uv", "venv", str(venv)])
        _run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(venv),
                str(core_wheel),
                "pytest",
                "hypothesis",
            ]
        )
        python = _venv_python(venv)
        _run([str(python), "-m", "pytest", "tests", "-o", "addopts="])
        probe = _run([str(python), "-c", f"import {PATRO_MODULE}"], check=False, capture=True)
        if probe.returncode == 0:
            raise GateError(f"{PATRO_MODULE} imported in a core-only venv")
        if "ModuleNotFoundError" not in probe.stderr:
            raise GateError(f"expected ModuleNotFoundError, got: {probe.stderr.strip()}")


def gate_patro_alone() -> None:
    """Check the two wheels agree on version and test the patro wheel on top of the core."""
    core_wheel = _find_archive(CORE_PREFIX, ".whl")
    patro_wheel = _find_archive(PATRO_PREFIX, ".whl")
    core_metadata = _wheel_metadata(core_wheel)
    patro_metadata = _wheel_metadata(patro_wheel)
    version = _metadata_version(core_metadata)
    if _metadata_version(patro_metadata) != version:
        raise GateError("core and patro wheels have different versions")

    expected_dep = _same_minor_range(version)
    found = False
    for line in patro_metadata.splitlines():
        if line.startswith("Requires-Dist:") and expected_dep in line:
            found = True
    if not found:
        raise GateError(f"patro wheel lacks Requires-Dist {expected_dep}")

    with tempfile.TemporaryDirectory() as tmp:
        venv = Path(tmp) / "venv"
        _run(["uv", "venv", str(venv)])
        _run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(venv),
                str(core_wheel),
                str(patro_wheel),
                "pytest",
                "hypothesis",
            ]
        )
        python = _venv_python(venv)
        _run([str(python), "-m", "pytest", "packages/nepdate-patro/tests", "-o", "addopts="])


def _same_minor_range(version: str) -> str:
    """Build the core dependency range a patro release must pin.

    Args:
        version: A ``major.minor.patch`` version.

    Returns:
        The ``nepdate>=major.minor,<major.(minor+1)`` requirement.
    """
    major, minor, _ = version.split(".")
    return f"nepdate>={major}.{minor},<{major}.{int(minor) + 1}"


GATES: tuple[tuple[str, Callable[[], None]], ...] = (
    ("ruff", gate_ruff),
    ("mypy", gate_mypy),
    ("pytest", gate_pytest),
    ("codegen", gate_codegen),
    ("import-time", gate_import_time),
    ("core alone", gate_core_alone),
    ("patro alone", gate_patro_alone),
)


def main(argv: list[str] | None = None) -> int:
    """Run the gates in order and print one summary line.

    Args:
        argv: Command line arguments. Defaults to ``sys.argv[1:]``.

    Returns:
        0 when every gate passes, 1 when a gate fails.
    """
    if argv is None:
        argv = sys.argv[1:]
    if argv:
        print(f"ci: unknown arguments {argv}", file=sys.stderr)
        return 2

    _run(["uv", "sync", "--all-packages"])
    for number, (name, gate) in enumerate(GATES, start=1):
        print(f"--- gate {number}: {name} ---")
        try:
            gate()
        except GateError as exc:
            print(f"ci: gate {number} ({name}) failed: {exc}")
            return 1
    print("ci: 7/7 gates passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

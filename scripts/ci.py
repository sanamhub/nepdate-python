"""Run every quality gate in order and stop at the first failure.

The entry point is ``uv run --locked python scripts/ci.py``; ``--locked`` makes a stale
``uv.lock`` fail instead of being rewritten. Each gate is defined in ADR-0004. Gates 6 and 7
install the wheels built from this checkout into throwaway virtualenvs and test each
distribution on its own, so a core-only install is proven to have no ``nepdate_patro``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"


def _project_name(pyproject: Path) -> str:
    """Read ``[project] name`` from a pyproject.toml.

    Args:
        pyproject: The pyproject.toml path.

    Returns:
        The distribution name as written.
    """
    with pyproject.open("rb") as f:
        name: str = tomllib.load(f)["project"]["name"]
    return name


def _archive_prefix(dist: str) -> str:
    """Return the file name prefix of a distribution's wheel and sdist (PEP 427, PEP 625).

    Args:
        dist: The distribution name.

    Returns:
        The normalized name with ``-`` and ``.`` as ``_``, followed by ``-``.
    """
    return dist.lower().replace("-", "_").replace(".", "_") + "-"


# The distribution names come from the pyproject files, so changing the core's PyPI name is an
# edit there only. The import names never change.
CORE_DIST = _project_name(ROOT / "pyproject.toml")
PATRO_DIST = _project_name(ROOT / "packages" / "nepdate-patro" / "pyproject.toml")
CORE_MODULE = "nepdate"
PATRO_MODULE = "nepdate_patro"
CORE_PREFIX = _archive_prefix(CORE_DIST)
PATRO_PREFIX = _archive_prefix(PATRO_DIST)
EVENT_ANCHOR = "World Day Against Human Trafficking"
# Coarse ceilings that catch a gross regression on a loaded CI runner. The ADR-0002 §7 budget
# (5 ms) is measured by the P5 benchmark on a quiet machine, not here.
CORE_IMPORT_LIMIT_US = 50_000
PATRO_IMPORT_LIMIT_US = 50_000
# The modules outside our own packages that `import nepdate` may add to a bare interpreter.
# dataclasses, and everything it pulls in, come from the frozen DateDiff dataclass
# (docs/API.md); the rest are what enum and datetime need.
CORE_IMPORT_ALLOWED = frozenset({
    "__future__",
    "_ast",
    "_datetime",
    "_opcode",
    "_opcode_metadata",
    "_sre",
    "_tokenize",
    "_typing",
    "_weakrefset",
    "ast",
    "copy",
    "copyreg",
    "dataclasses",
    "datetime",
    "dis",
    "enum",
    "importlib",
    "importlib._bootstrap",
    "importlib._bootstrap_external",
    "importlib.machinery",
    "inspect",
    "opcode",
    "re",
    "re._casefix",
    "re._compiler",
    "re._constants",
    "re._parser",
    "token",
    "tokenize",
    "typing",
    "weakref",
})
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
            f"--cov={CORE_MODULE}",
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
            f"--include=*/{CORE_MODULE}/*",
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


def _new_modules(setup: str, statement: str) -> set[str]:
    """Return the modules that a statement adds to ``sys.modules`` after a setup statement.

    Args:
        setup: Code that runs first; its modules count as already loaded.
        statement: The import whose new modules are returned.

    Returns:
        The module names that appeared while the statement ran.
    """
    script = "; ".join(
        [
            "import sys",
            setup or "pass",
            "base = set(sys.modules)",
            statement,
            "print(' '.join(sorted(set(sys.modules) - base)))",
        ]
    )
    result = _run(["uv", "run", "python", "-c", script], capture=True)
    return set(result.stdout.split())


def _outside(modules: set[str], package: str, allowed: frozenset[str]) -> list[str]:
    """Return the modules that are neither in the package nor allowed.

    Args:
        modules: The module names to check.
        package: The top-level package whose own modules are always allowed.
        allowed: Other module names that may appear.

    Returns:
        The offending module names, sorted.
    """
    return sorted(
        m for m in modules if m != package and not m.startswith(f"{package}.") and m not in allowed
    )


def gate_import_time() -> None:
    """Check what each import loads, that the core never loads the patro, and a coarse ceiling."""
    core_new = _new_modules("", f"import {CORE_MODULE}")
    if extra := _outside(core_new, CORE_MODULE, CORE_IMPORT_ALLOWED):
        raise GateError(f"import {CORE_MODULE} loaded unexpected modules: {', '.join(extra)}")
    if PATRO_MODULE in core_new:
        raise GateError(f"import {CORE_MODULE} loaded {PATRO_MODULE}")
    patro_new = _new_modules(f"import {CORE_MODULE}", f"import {PATRO_MODULE}")
    if extra := _outside(patro_new, PATRO_MODULE, frozenset()):
        raise GateError(f"import {PATRO_MODULE} loaded unexpected modules: {', '.join(extra)}")
    core_us, _ = _import_time(f"import {CORE_MODULE}", CORE_MODULE)
    if core_us >= CORE_IMPORT_LIMIT_US:
        raise GateError(f"import {CORE_MODULE} takes {core_us} us, limit {CORE_IMPORT_LIMIT_US}")
    patro_us, _ = _import_time(f"import {CORE_MODULE}; import {PATRO_MODULE}", PATRO_MODULE)
    if patro_us >= PATRO_IMPORT_LIMIT_US:
        raise GateError(f"import {PATRO_MODULE} takes {patro_us} us, limit {PATRO_IMPORT_LIMIT_US}")
    print(f"ci: import {CORE_MODULE} {core_us} us, {PATRO_MODULE} {patro_us} us (not a benchmark)")


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
        The ``<core>>=major.minor,<major.(minor+1)`` requirement, ``<core>`` being the core
        distribution name.
    """
    major, minor, _ = version.split(".")
    return f"{CORE_DIST}>={major}.{minor},<{major}.{int(minor) + 1}"


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

    # Every uv call below must use uv.lock as committed: a pyproject change without a lock update
    # fails here instead of being re-locked silently.
    os.environ["UV_LOCKED"] = "1"
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

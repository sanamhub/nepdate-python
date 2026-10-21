"""Run every quality gate in order and stop at the first failure.

The entry point is ``uv run --locked python scripts/ci.py``; ``--locked`` makes a stale
``uv.lock`` fail instead of being rewritten. Gates 1 to 9 are defined in ADR-0004 and ADR-0006;
gate 10 is the API snapshot from ADR-0010. Gates 6 and 7 install the wheels built from this
checkout into throwaway virtualenvs and test each distribution on its own, so a core-only install
is proven to have no ``nepdate_patro``.
"""

from __future__ import annotations

import datetime
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import data_status
import rehearsal
import versions

ROOT = Path(__file__).resolve().parent.parent
# scripts/ci_matrix.py runs several versions at once in this checkout; each gets its own folder.
DIST = Path(os.environ.get("NEPDATE_CI_DIST") or ROOT / "dist")


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


def _project_table(pyproject: Path) -> dict[str, Any]:
    """Read the ``[project]`` table from a pyproject.toml.

    Args:
        pyproject: The pyproject.toml path.

    Returns:
        The project table.
    """
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    project = data["project"]
    assert isinstance(project, dict)
    return project


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
# (5 ms) is measured by the benchmark suite on a quiet machine, not here (ADR-0006).
CORE_IMPORT_LIMIT_US = 50_000
PATRO_IMPORT_LIMIT_US = 50_000
# The only modules outside our own packages that `import nepdate` may add to a bare interpreter.
# Widen this only with a reason in the commit; dataclasses alone adds 27 modules
# and breaks the ADR-0002 §7 budget, so value types are written by hand. `operator` is here
# because the constructor validates with operator.index (ADR-0002); before 3.14 the interpreter
# had already loaded it at startup, so the gate never saw it.
CORE_IMPORT_ALLOWED = frozenset({"__future__", "_datetime", "datetime", "enum", "operator"})
COVERAGE_MIN = 90
IMPORT_TIME_FIELDS = 3
TODAY_OPTION_PARTS = 2


class GateError(Exception):
    """Raised when a gate fails, carrying a human-readable reason."""


def _run(
    cmd: list[str], *, check: bool = True, capture: bool = False, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a command from the repository root and print it first.

    Args:
        cmd: The command and its arguments, no shell involved.
        check: Raise GateError when the command exits non-zero.
        capture: Capture stdout and stderr instead of streaming them.
        cwd: The working directory; defaults to the repository root.

    Returns:
        The completed process, with stdout and stderr as text.

    Raises:
        GateError: The command exited non-zero and ``check`` is true.
    """
    print("+", " ".join(cmd))
    result = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=capture, text=True, check=False)
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
            "README.md",
            "packages/nepdate-patro/README.md",
            "--doctest-glob=README.md",
            "--import-mode=importlib",
            "--doctest-modules",
            "src/nepdate/_date.py",
            "src/nepdate/_range.py",
            "packages/nepdate-patro/src/nepdate_patro/__init__.py",
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
    # What the allowed stdlib modules load themselves differs by version (datetime pulls in
    # math on 3.11), so it is measured on this interpreter instead of listed.
    stdlib_deps = _new_modules("", "import " + ", ".join(sorted(CORE_IMPORT_ALLOWED)))
    if extra := _outside(core_new, CORE_MODULE, CORE_IMPORT_ALLOWED | stdlib_deps):
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
    _run(["uv", "build", "--all-packages", "--out-dir", str(DIST)])
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

    specifiers = _requirement_specifiers(patro_metadata, CORE_DIST)
    expected = versions.core_specifiers(versions.to_semver(version))
    if specifiers != expected:
        raise GateError(
            f"patro wheel requires {CORE_DIST} with {sorted(specifiers)}, "
            f"expected {sorted(expected)}"
        )

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


def gate_docs() -> None:
    """Check the README, changelog, community files and top-level docs pages."""
    _run(["uv", "run", "python", "scripts/docs_check.py"])


def gate_api() -> None:
    """Check the public surface against the committed API snapshot."""
    _run(["uv", "run", "python", "scripts/api_snapshot.py", "--check"])


def gate_consumer() -> None:
    """Install both built wheels in a fresh venv outside the repo and use each one."""
    core_wheel = _find_archive(CORE_PREFIX, ".whl")
    patro_wheel = _find_archive(PATRO_PREFIX, ".whl")
    with tempfile.TemporaryDirectory() as tmp:
        outside = Path(tmp) / "consumer"
        outside.mkdir()
        venv = outside / "venv"
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
            ]
        )
        code = (
            "from nepdate import NepaliDate\n"
            "from nepdate_patro import info\n"
            "d = NepaliDate(2080, 5, 15)\n"
            "assert d.to_date().isoformat() == '2023-09-01'\n"
            "assert info(d).tithi.label() == 'Dwitiya'\n"
            "print('consumer: one conversion and one patro lookup passed')\n"
        )
        _run([str(_venv_python(venv)), "-c", code], cwd=outside)


def _unreleased_errors(text: str) -> list[str]:
    """Check that the ``[Unreleased]`` changelog section has no entries.

    Args:
        text: The ``CHANGELOG.md`` contents.

    Returns:
        One message when the section has content; an empty list otherwise.
    """
    heading = re.search(r"^## \[Unreleased\][ \t]*$", text, re.MULTILINE)
    if heading is None:
        return []
    rest = text[heading.end() :]
    following = re.search(r"^## \[", rest, re.MULTILINE)
    body = rest[: following.start()] if following else rest
    if not body.strip():
        return []
    return ["CHANGELOG.md has entries under [Unreleased]; move them into the dated release section"]


def _changelog_errors(version: str, root: Path) -> list[str]:
    """Check the dated changelog heading for one version and an empty ``[Unreleased]``.

    Args:
        version: The released ``X.Y.Z`` version.
        root: The repository root.

    Returns:
        One message per problem; an empty list when the section is present, dated and
        ``[Unreleased]`` is empty.
    """
    changelog = root / "CHANGELOG.md"
    if not changelog.is_file():
        return ["CHANGELOG.md is missing"]
    text = changelog.read_text(encoding="utf-8")
    errors: list[str] = []
    heading = re.search(
        rf"^## \[{re.escape(version)}\] - ([0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}})$",
        text,
        re.MULTILINE,
    )
    if heading is None:
        errors.append(f"CHANGELOG.md has no '## [{version}] - YYYY-MM-DD' section")
    else:
        try:
            datetime.date.fromisoformat(heading.group(1))
        except ValueError:
            errors.append(f"CHANGELOG.md has an invalid date: {heading.group(1)}")
    errors.extend(_unreleased_errors(text))
    return errors


def release_check(  # noqa: PLR0912 - one branch per release file family
    version: str,
    root: Path = ROOT,
    *,
    today: datetime.date | None = None,
    warnings: list[str] | None = None,
    data: bool = True,
) -> list[str]:
    """Check the version, the dependencies, the changelog and the patro data freshness.

    Args:
        version: The semver version being released, as in the tag and the changelog
            (``0.1.0`` or ``0.1.0-beta.1``). The pyprojects carry its PEP 440 form.
        root: The repository root. Tests pass a temporary copy.
        today: The AD date for the data freshness check; today's UTC date when None.
        warnings: When given, receives the tithi and event warnings.
        data: Whether to run the data freshness check. Only tests of the version rules turn it
            off; a missing patro folder is an error, never a skipped check.

    Returns:
        One message per inconsistency; an empty list means the release is consistent.
    """
    if not versions.is_semver(version):
        return [f"not a release version (X.Y.Z or X.Y.Z-alpha|beta|rc.N): {version}"]
    pypi_version = versions.to_pep440(version)
    errors: list[str] = []
    core_path = root / "pyproject.toml"
    patro_path = root / "packages" / "nepdate-patro" / "pyproject.toml"
    core_project = _project_table(core_path)
    patro_project = _project_table(patro_path)
    core_name = core_project.get("name")
    if not isinstance(core_name, str):
        errors.append("core pyproject has no name")
        core_name = CORE_DIST
    for label, project in (("core", core_project), ("patro", patro_project)):
        actual = project.get("version")
        if actual != pypi_version:
            errors.append(f"{label} pyproject version is {actual!r}, expected {pypi_version!r}")
    dependencies = patro_project.get("dependencies", [])
    if not isinstance(dependencies, list):
        errors.append("patro dependencies is not a list")
        dependencies = []
    specifiers: set[str] = set()
    for dependency in dependencies:
        if isinstance(dependency, str):
            found = _requirement_specifiers(f"Requires-Dist: {dependency}", core_name)
            if found:
                specifiers = found
                break
    expected = versions.core_specifiers(version)
    if specifiers != expected:
        errors.append(
            f"patro requires {core_name} with {sorted(specifiers)}, expected {sorted(expected)}"
        )
    errors.extend(_changelog_errors(version, root))
    if data:
        try:
            report = data_status.diagnose(root, today)
        except data_status.DataError as exc:
            errors.append(str(exc))
        else:
            errors.extend(report.failures)
            if warnings is not None:
                warnings.extend(report.warnings)
    return errors


def release_notes(version: str, root: Path = ROOT) -> str:
    """Return the GitHub Release body: the changelog section, then install and verify steps.

    The notes come from the changelog, not the commit log, so a release page says what a package
    user gets rather than how the work happened.

    Args:
        version: The released semver version, as in the tag and the changelog.
        root: The repository root.

    Returns:
        The section body without its heading, followed by the Install and Verification blocks.

    Raises:
        GateError: The changelog has no matching section.
    """
    text = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    heading = re.search(rf"^## \[{re.escape(version)}\] - .*$", text, re.MULTILINE)
    if heading is None:
        raise GateError(f"CHANGELOG.md has no section for {version}")
    rest = text[heading.end() :]
    following = re.search(r"^## \[", rest, re.MULTILINE)
    body = rest[: following.start()] if following else rest
    pypi_version = versions.to_pep440(version)
    pre = " --pre" if versions.is_prerelease(version) else ""
    core_wheel = f"{_archive_prefix(CORE_DIST)}{pypi_version}-py3-none-any.whl"
    return (
        f"{body.strip()}\n\n"
        "### Install\n\n"
        "```\n"
        f"pip install{pre} {CORE_DIST}=={pypi_version} {PATRO_DIST}=={pypi_version}\n"
        "```\n\n"
        f"The import names are `{CORE_MODULE}` and `{PATRO_MODULE}`. Install only "
        f"`{CORE_DIST}` if you do not need tithi, holidays or events.\n\n"
        "### Verification\n\n"
        "- Both distributions were uploaded by this tag's release workflow with PyPI trusted\n"
        "  publishing, so no API token exists for this project. PyPI keeps a provenance\n"
        "  attestation for every file; to check one:\n\n"
        "  ```\n"
        "  pip install pypi-attestations\n"
        "  pypi-attestations verify pypi --repository "
        f"https://github.com/sanamhub/nepdate-python pypi:{core_wheel}\n"
        "  ```\n\n"
        "- After the upload, the workflow installed both from PyPI on Linux, macOS and Windows\n"
        "  with Python 3.11 and 3.14 and checked one conversion and one patro lookup.\n"
    )


def sort_dist(root: Path = ROOT) -> None:
    """Move the built files into ``dist/core/`` and ``dist/patro/``.

    Args:
        root: The repository root.

    Raises:
        GateError: An artifact does not belong to either distribution.
    """
    dist = root / "dist"
    core_prefix = _archive_prefix(_project_name(root / "pyproject.toml"))
    patro_prefix = _archive_prefix(
        _project_name(root / "packages" / "nepdate-patro" / "pyproject.toml")
    )
    core_dir = dist / "core"
    patro_dir = dist / "patro"
    core_dir.mkdir(parents=True, exist_ok=True)
    patro_dir.mkdir(parents=True, exist_ok=True)
    for artifact in sorted(dist.iterdir()):
        if not artifact.is_file():
            continue
        if artifact.name.startswith(core_prefix):
            target = core_dir
        elif artifact.name.startswith(patro_prefix):
            target = patro_dir
        else:
            raise GateError(f"unknown artifact in dist: {artifact.name}")
        shutil.move(str(artifact), str(target / artifact.name))
        print(f"release: {artifact.name} -> {target.relative_to(root)}")


def _requirement_specifiers(metadata: str, distribution: str) -> set[str]:
    """Return the version specifiers of a wheel's first requirement on ``distribution``.

    The set comparison is deliberate: ``Requires-Dist`` may list the specifiers in any order.

    Args:
        metadata: The wheel ``METADATA`` contents.
        distribution: The distribution name to find.

    Returns:
        The specifier strings, or an empty set when no requirement names the distribution.
    """
    for line in metadata.splitlines():
        if not line.startswith("Requires-Dist:"):
            continue
        requirement = line.split(":", 1)[1].strip()
        if not requirement.startswith(distribution):
            continue
        boundary = requirement[len(distribution) : len(distribution) + 1]
        if boundary and boundary not in "<>=!~[ (":
            continue
        rest = requirement[len(distribution) :].split(";", 1)[0].strip()
        if rest.startswith("(") and rest.endswith(")"):
            rest = rest[1:-1]
        return {part.strip() for part in rest.split(",") if part.strip()}
    return set()


GATES: tuple[tuple[str, Callable[[], None]], ...] = (
    ("ruff", gate_ruff),
    ("mypy", gate_mypy),
    ("pytest", gate_pytest),
    ("codegen", gate_codegen),
    ("import-time", gate_import_time),
    ("core alone", gate_core_alone),
    ("patro alone", gate_patro_alone),
    ("docs", gate_docs),
    ("consumer", gate_consumer),
    ("api", gate_api),
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
        return _run_command(argv)

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
    print(f"ci: {len(GATES)}/{len(GATES)} gates passed")
    return 0


def _release_today(options: list[str]) -> datetime.date | None:
    """Read an optional ``--today YYYY-MM-DD`` release option.

    Args:
        options: The arguments after the version.

    Returns:
        The parsed date, or None when the option is absent.

    Raises:
        ValueError: The option is malformed or the date is not real.
    """
    if not options:
        return None
    if len(options) != TODAY_OPTION_PARTS or options[0] != "--today":
        raise ValueError(f"expected --today YYYY-MM-DD, got {' '.join(options)}")
    return datetime.date.fromisoformat(options[1])


def _run_command(argv: list[str]) -> int:  # noqa: PLR0911, PLR0912 - one branch per command
    """Run a release helper command.

    Args:
        argv: ``release-check VERSION [--today DATE]``, ``release-notes VERSION``,
            ``pypi-version VERSION``, ``data-status``, ``release-rehearsal [VERSION]``,
            ``build-release`` or ``sort-dist``.

    Returns:
        0 on success, 1 on a release inconsistency, 2 on an unknown or bad command.
    """
    command, *rest = argv
    if command == "release-check" and rest:
        try:
            today = _release_today(rest[1:])
        except ValueError as exc:
            print(f"release: {exc}", file=sys.stderr)
            return 2
        warnings: list[str] = []
        errors = release_check(rest[0], today=today, warnings=warnings)
        for warning in warnings:
            print(f"release: WARNING: {warning}")
        for error in errors:
            print(f"release: {error}", file=sys.stderr)
        if errors:
            return 1
        print(f"release: {rest[0]} is consistent")
        return 0
    if command == "pypi-version" and len(rest) == 1:
        try:
            print(versions.to_pep440(rest[0]))
        except ValueError as exc:
            print(f"release: {exc}", file=sys.stderr)
            return 1
        return 0
    if command == "data-status":
        return data_status.main(rest)
    if command == "release-rehearsal":
        return rehearsal.main(rest)
    if command == "build-release" and not rest:
        try:
            artifacts = rehearsal.build_artifacts(ROOT, DIST)
        except rehearsal.RehearsalError as exc:
            print(f"release: {exc}", file=sys.stderr)
            return 1
        for artifact in artifacts:
            print(f"release: built {artifact.name}")
        return 0
    if command == "release-notes" and len(rest) == 1:
        try:
            sys.stdout.write(release_notes(rest[0]))
        except GateError as exc:
            print(f"release: {exc}", file=sys.stderr)
            return 1
    elif command == "sort-dist" and not rest:
        try:
            sort_dist()
        except GateError as exc:
            print(f"release: {exc}", file=sys.stderr)
            return 1
    else:
        print(f"ci: unknown arguments {argv}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

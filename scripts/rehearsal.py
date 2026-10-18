"""Build and check the four release artifacts without uploading anything.

The release build stages the patro source data next to the patro package, so the sdist carries the
JSON the generated table comes from. The wheels are checked to contain only their package and
dist-info, the sdists are checked for the licence and source data, and ``twine check`` reads the
metadata of all four files.
"""

from __future__ import annotations

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

ROOT = Path(__file__).resolve().parent.parent
VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
VERSION_LITERAL = re.compile(r"""__version__\s*=\s*["']([^"']+)["']""")
CHANGELOG = re.compile(r"^## \[([^\]]+)\] - ([0-9]{4}-[0-9]{2}-[0-9]{2})$", re.MULTILINE)
FORBIDDEN = frozenset({"tests", "fuzz", "docs"})
CORE_SDIST = (
    "LICENSE",
    "shared/data/NOTICE",
    "shared/data/calendar/bs-calendar.json",
)
PATRO_SDIST = (
    "LICENSE",
    "NOTICE",
    "shared/data/patro/2077.json",
    "src/nepdate_patro/_tables.py",
)
TWINE_GROUP = "release"
ARTIFACT_COUNT = 4


class RehearsalError(Exception):
    """Raised when an artifact cannot be built or read."""


def _project(path: Path) -> dict[str, object]:
    """Read the ``[project]`` table from a pyproject file.

    Args:
        path: The pyproject path.

    Returns:
        The project table.

    Raises:
        RehearsalError: The file is missing or has no project table.
    """
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise RehearsalError(f"cannot read {path}: {exc}") from exc
    project = data.get("project")
    if not isinstance(project, dict):
        raise RehearsalError(f"{path}: no [project] table")
    return project


def project_version(root: Path = ROOT) -> str:
    """Return the one version both pyprojects declare.

    Args:
        root: The repository root.

    Returns:
        The version string.

    Raises:
        RehearsalError: A version is missing, invalid or different between the two projects.
    """
    core = _project(root / "pyproject.toml").get("version")
    patro = _project(root / "packages" / "nepdate-patro" / "pyproject.toml").get("version")
    if not isinstance(core, str) or not VERSION.fullmatch(core):
        raise RehearsalError(f"core version is not X.Y.Z: {core!r}")
    if patro != core:
        raise RehearsalError(f"patro version {patro!r} differs from core {core!r}")
    return core


def _distribution_name(root: Path, package: str) -> str:
    """Return a distribution name from one pyproject.

    Args:
        root: The repository root.
        package: ``core`` or ``patro``.

    Returns:
        The distribution name.
    """
    path = root / "pyproject.toml"
    if package == "patro":
        path = root / "packages" / "nepdate-patro" / "pyproject.toml"
    name = _project(path).get("name")
    if not isinstance(name, str):
        raise RehearsalError(f"{path}: no project name")
    return name


def _prefix(name: str) -> str:
    """Return the archive prefix of a distribution name.

    Args:
        name: The distribution name.

    Returns:
        The normalized name with a trailing hyphen.
    """
    return name.lower().replace("-", "_").replace(".", "_") + "-"


def _changelog_errors(version: str, root: Path) -> list[str]:
    """Check that the changelog has a dated top section for the version.

    Args:
        version: The released version.
        root: The repository root.

    Returns:
        One message per problem; an empty list when the section is present.
    """
    path = root / "CHANGELOG.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read {path}: {exc}"]
    for match in CHANGELOG.finditer(text):
        if match.group(1) == version:
            return []
    return [f"CHANGELOG.md has no '## [{version}] - YYYY-MM-DD' section"]


def _version_literal_errors(version: str, root: Path) -> list[str]:
    """Check any literal ``__version__`` in the two packages against the release version.

    Args:
        version: The released version.
        root: The repository root.

    Returns:
        One message per literal that does not match; an empty list when there is none.
    """
    found: list[str] = []
    for relative in (
        "src/nepdate/__init__.py",
        "packages/nepdate-patro/src/nepdate_patro/__init__.py",
    ):
        path = root / relative
        text = path.read_text(encoding="utf-8")
        for match in VERSION_LITERAL.finditer(text):
            if match.group(1) != version:
                found.append(f"{relative} has __version__ {match.group(1)!r}, expected {version!r}")
    return found


def check_versions(version: str, root: Path = ROOT) -> list[str]:
    """Check the pyprojects, the changelog and any version literal in ``__init__``.

    Args:
        version: The version being released.
        root: The repository root.

    Returns:
        One message per inconsistency; an empty list means the versions agree.
    """
    errors: list[str] = []
    try:
        actual = project_version(root)
    except RehearsalError as exc:
        errors.append(str(exc))
    else:
        if actual != version:
            errors.append(f"pyproject versions are {actual!r}, expected {version!r}")
    errors.extend(_changelog_errors(version, root))
    errors.extend(_version_literal_errors(version, root))
    return errors


def _members(path: Path) -> list[str]:
    """Return the member names of a wheel or sdist.

    Args:
        path: The archive path.

    Returns:
        The member names.

    Raises:
        RehearsalError: The archive cannot be read.
    """
    try:
        if path.suffix == ".whl":
            with zipfile.ZipFile(path) as archive:
                return archive.namelist()
        with tarfile.open(path, "r:gz") as archive:
            return [member.name for member in archive.getmembers() if member.isfile()]
    except (OSError, zipfile.BadZipFile, tarfile.TarError) as exc:
        raise RehearsalError(f"cannot read {path}: {exc}") from exc


def _metadata_version(path: Path) -> str:
    """Read the version from a wheel's METADATA.

    Args:
        path: The wheel path.

    Returns:
        The version string, or an empty string when METADATA is absent.

    Raises:
        RehearsalError: The wheel cannot be read.
    """
    try:
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if not name.endswith(".dist-info/METADATA"):
                    continue
                for line in archive.read(name).decode("utf-8").splitlines():
                    if line.startswith("Version:"):
                        return line.split(":", 1)[1].strip()
    except (OSError, zipfile.BadZipFile) as exc:
        raise RehearsalError(f"cannot read {path}: {exc}") from exc
    return ""


def check_wheel(wheel: Path, module: str, version: str) -> list[str]:
    """Check one wheel's members and metadata version.

    Args:
        wheel: The wheel path.
        module: The import package the wheel must contain.
        version: The expected version.

    Returns:
        One message per problem; an empty list means the wheel passes.

    Raises:
        RehearsalError: The wheel cannot be read.
    """
    errors: list[str] = []
    metadata = _metadata_version(wheel)
    if metadata != version:
        errors.append(f"{wheel.name}: METADATA version {metadata!r}, expected {version!r}")
    for name in _members(wheel):
        parts = name.split("/")
        if any(part in FORBIDDEN for part in parts):
            errors.append(f"{wheel.name}: forbidden path {name}")
        if parts[-1].startswith("test_") and parts[-1].endswith(".py"):
            errors.append(f"{wheel.name}: test file {name}")
        if not (name.startswith(f"{module}/") or ".dist-info/" in name):
            errors.append(f"{wheel.name}: unexpected member {name}")
    return errors


def check_sdist(sdist: Path, required: tuple[str, ...]) -> list[str]:
    """Check that an sdist has the licence files and shared source data.

    Args:
        sdist: The sdist path.
        required: Paths relative to the archive's top directory.

    Returns:
        One message per missing path; an empty list means the sdist passes.

    Raises:
        RehearsalError: The sdist cannot be read.
    """
    names = _members(sdist)
    return [
        f"{sdist.name}: missing {path}"
        for path in required
        if not any(name.endswith(f"/{path}") for name in names)
    ]


def _tail(text: str, lines: int = 12) -> str:
    """Return the last non-empty lines of text.

    Args:
        text: The command output.
        lines: The number of lines to keep.

    Returns:
        The selected lines, joined by newlines.
    """
    kept = [line for line in text.splitlines() if line.strip()]
    return "\n".join(kept[-lines:])


def _run_twine(files: list[Path], root: Path) -> subprocess.CompletedProcess[str]:
    """Run ``twine check`` from the pinned release group.

    Args:
        files: The artifacts to check.
        root: The repository root.

    Returns:
        The completed command.
    """
    command = ["uv", "run", "--group", TWINE_GROUP, "twine", "check", *map(str, files)]
    return subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)


def twine_check(
    files: list[Path],
    root: Path = ROOT,
    runner: Callable[[list[Path], Path], subprocess.CompletedProcess[str]] = _run_twine,
) -> list[str]:
    """Check the artifacts with twine.

    Args:
        files: The four artifacts.
        root: The repository root.
        runner: The command runner, replaced in tests.

    Returns:
        One message when twine fails; an empty list when it passes.
    """
    result = runner(files, root)
    if result.returncode == 0:
        return []
    output = (result.stdout + result.stderr).strip()
    return [f"twine check failed ({result.returncode}): {_tail(output)}"]


def _stage_text(root: Path, stage: Path) -> None:
    """Copy the files a release build needs and stage the patro source data.

    Args:
        root: The repository root.
        stage: The empty staging directory.

    Raises:
        RehearsalError: A required file or directory is missing.
    """
    copies = ("pyproject.toml", "uv.lock", "README.md", "LICENSE", "CHANGELOG.md")
    for name in copies:
        source = root / name
        if not source.is_file():
            raise RehearsalError(f"missing {source}")
        shutil.copy2(source, stage / name)
    for relative in ("src", "packages/nepdate-patro", "shared/data"):
        source = root / relative
        if not source.is_dir():
            raise RehearsalError(f"missing {source}")
        shutil.copytree(
            source,
            stage / relative,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".venv"),
        )
    patro_pyproject = stage / "packages" / "nepdate-patro" / "pyproject.toml"
    text = patro_pyproject.read_text(encoding="utf-8")
    marker = '[tool.uv.build-backend]\nmodule-name = "nepdate_patro"\n'
    if marker not in text:
        raise RehearsalError("patro pyproject has no build-backend block")
    text = text.replace(marker, marker + 'source-include = ["shared/data/patro/**"]\n', 1)
    patro_pyproject.write_text(text, encoding="utf-8", newline="\n")
    target = stage / "packages" / "nepdate-patro" / "shared" / "data" / "patro"
    shutil.copytree(stage / "shared" / "data" / "patro", target)


def build_artifacts(root: Path, out_dir: Path) -> list[Path]:
    """Build both sdists and both wheels into ``out_dir``.

    Args:
        root: The repository root.
        out_dir: The output directory, cleared first.

    Returns:
        The four artifact paths, sorted.

    Raises:
        RehearsalError: The build fails or does not produce four files.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p10-build-") as tmp:
        stage = Path(tmp) / "repo"
        stage.mkdir()
        _stage_text(root, stage)
        result = subprocess.run(
            [
                "uv",
                "build",
                "--all-packages",
                "--out-dir",
                str(out_dir),
                "--clear",
                "--no-create-gitignore",
            ],
            cwd=stage,
            capture_output=True,
            text=True,
            check=False,
        )
    if result.returncode != 0:
        raise RehearsalError(f"uv build failed: {_tail(result.stdout + result.stderr)}")
    artifacts = sorted(path for path in out_dir.glob("*") if path.suffix in {".whl", ".gz"})
    if len(artifacts) != ARTIFACT_COUNT:
        raise RehearsalError(
            f"expected {ARTIFACT_COUNT} artifacts, found {len(artifacts)} in {out_dir}"
        )
    return artifacts


def _pick(artifacts: list[Path], prefix: str, suffix: str) -> Path:
    """Return the one artifact with a prefix and suffix.

    Args:
        artifacts: The built files.
        prefix: The normalized distribution prefix.
        suffix: The file suffix.

    Returns:
        The matching path.

    Raises:
        RehearsalError: There is not exactly one match.
    """
    matches = [
        path for path in artifacts if path.name.startswith(prefix) and path.name.endswith(suffix)
    ]
    if len(matches) != 1:
        raise RehearsalError(f"expected one {prefix}*{suffix}, found {len(matches)}")
    return matches[0]


def install_versions(core: Path, patro: Path, version: str, root: Path) -> list[str]:
    """Install both wheels without dependencies and read their metadata versions.

    Args:
        core: The core wheel.
        patro: The patro wheel.
        version: The expected version.
        root: The repository root.

    Returns:
        One message per mismatch; an empty list when the installed metadata agrees.
    """
    core_name = _distribution_name(root, "core")
    patro_name = _distribution_name(root, "patro")
    with tempfile.TemporaryDirectory(prefix="p10-install-") as tmp:
        venv = Path(tmp) / "venv"
        for command in (
            ["uv", "venv", str(venv)],
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(venv),
                "--no-deps",
                str(core),
                str(patro),
            ],
        ):
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                return [f"install failed: {_tail(result.stdout + result.stderr)}"]
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        code = (
            "import importlib.metadata as m\n"
            f"print(m.version({core_name!r}))\n"
            f"print(m.version({patro_name!r}))\n"
        )
        result = subprocess.run(
            [str(python), "-c", code], cwd=root, capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            return [f"metadata read failed: {_tail(result.stderr)}"]
        found = result.stdout.split()
        if found != [version, version]:
            return [f"installed metadata reports {found}, expected {[version, version]}"]
    return []


def _version_errors(version: str) -> list[str]:
    """Check the version shape before a build.

    Args:
        version: The version being released.

    Returns:
        One message when the version is not ``X.Y.Z``.
    """
    return [] if VERSION.fullmatch(version) else [f"not a strict semver: {version}"]


def rehearse(version: str, root: Path = ROOT) -> list[str]:
    """Build and check the four release artifacts.

    Args:
        version: The version being released.
        root: The repository root.

    Returns:
        One message per failure; an empty list means the rehearsal passed.
    """
    errors = _version_errors(version)
    errors.extend(check_versions(version, root))
    if errors:
        return errors
    with tempfile.TemporaryDirectory(prefix="p10-rehearsal-") as tmp:
        out_dir = Path(tmp) / "dist"
        try:
            artifacts = build_artifacts(root, out_dir)
        except RehearsalError as exc:
            return [str(exc)]
        core_prefix = _prefix(_distribution_name(root, "core"))
        patro_prefix = _prefix(_distribution_name(root, "patro"))
        try:
            core_wheel = _pick(artifacts, core_prefix, ".whl")
            core_sdist = _pick(artifacts, core_prefix, ".tar.gz")
            patro_wheel = _pick(artifacts, patro_prefix, ".whl")
            patro_sdist = _pick(artifacts, patro_prefix, ".tar.gz")
        except RehearsalError as exc:
            return [str(exc)]
        for artifact in artifacts:
            print(f"release: built {artifact.name}")
        errors.extend(twine_check(artifacts, root))
        errors.extend(check_wheel(core_wheel, "nepdate", version))
        errors.extend(check_wheel(patro_wheel, "nepdate_patro", version))
        errors.extend(check_sdist(core_sdist, CORE_SDIST))
        errors.extend(check_sdist(patro_sdist, PATRO_SDIST))
        errors.extend(install_versions(core_wheel, patro_wheel, version, root))
    if not errors:
        print(f"release: {ARTIFACT_COUNT} artifacts checked")
    return errors


def main(argv: list[str] | None = None) -> int:
    """Run the rehearsal for one version.

    Args:
        argv: ``[VERSION]``; the pyproject version when omitted.

    Returns:
        0 when the rehearsal passes, 1 on a failure, 2 on bad arguments.
    """
    args = list(argv if argv is not None else [])
    if len(args) > 1:
        print("release: rehearsal takes at most one version", file=sys.stderr)
        return 2
    try:
        version = args[0] if args else project_version()
    except RehearsalError as exc:
        print(f"release: {exc}", file=sys.stderr)
        return 1
    errors = rehearse(version)
    for error in errors:
        print(f"release: {error}", file=sys.stderr)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

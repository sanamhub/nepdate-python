"""Release rehearsal checks on synthetic wheels, sdists and a temporary source tree."""

from __future__ import annotations

import io
import subprocess
import tarfile
import zipfile
from pathlib import Path
from typing import Any

import pytest


def _wheel(path: Path, version: str, extra: tuple[str, ...] = ()) -> None:
    """Write a small wheel.

    Args:
        path: The wheel path.
        version: The METADATA version.
        extra: Extra member names.
    """
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("nepdate/__init__.py", "")
        archive.writestr(
            f"nepdate_core-{version}.dist-info/METADATA",
            f"Metadata-Version: 2.4\nName: nepdate-core\nVersion: {version}\n",
        )
        for name in extra:
            archive.writestr(name, "")


def _sdist(path: Path, members: tuple[str, ...]) -> None:
    """Write a small sdist.

    Args:
        path: The sdist path.
        members: Member names.
    """
    with tarfile.open(path, "w:gz") as archive:
        for name in members:
            data = b"x"
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))


def _release(root: Path, version: str = "0.1.0", literal: str | None = None) -> None:
    """Write the minimal release files ``check_versions`` reads.

    Args:
        root: The temporary repository root.
        version: The version in both pyprojects and the changelog.
        literal: An optional ``__version__`` literal in the core init.
    """
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "nepdate-core"\nversion = "{version}"\n', encoding="utf-8"
    )
    patro = root / "packages" / "nepdate-patro"
    patro.mkdir(parents=True)
    (patro / "pyproject.toml").write_text(
        f'[project]\nname = "nepdate-patro"\nversion = "{version}"\n', encoding="utf-8"
    )
    (root / "CHANGELOG.md").write_text(
        f"# Changelog\n\n## [{version}] - 2026-10-18\n\n- Release.\n", encoding="utf-8"
    )
    init = root / "src" / "nepdate" / "__init__.py"
    init.parent.mkdir(parents=True)
    init.write_text(f'__version__ = "{literal}"\n' if literal is not None else "", encoding="utf-8")
    patro_init = patro / "src" / "nepdate_patro" / "__init__.py"
    patro_init.parent.mkdir(parents=True)
    patro_init.write_text("", encoding="utf-8")


def test_clean_wheel_passes(rehearsal: Any, tmp_path: Path) -> None:
    """A package plus dist-info is the whole wheel."""
    wheel = tmp_path / "nepdate_core-0.1.0-py3-none-any.whl"
    _wheel(wheel, "0.1.0")
    assert rehearsal.check_wheel(wheel, "nepdate", "0.1.0") == []


def test_wheel_with_tests_member_fails(rehearsal: Any, tmp_path: Path) -> None:
    """A tests directory in the wheel is a failure, not a curious extra."""
    wheel = tmp_path / "nepdate_core-0.1.0-py3-none-any.whl"
    _wheel(wheel, "0.1.0", ("tests/test_x.py",))
    errors = rehearsal.check_wheel(wheel, "nepdate", "0.1.0")
    assert any("forbidden path tests/test_x.py" in error for error in errors)
    assert any("test file tests/test_x.py" in error for error in errors)


def test_wheel_with_a_docs_file_fails(rehearsal: Any, tmp_path: Path) -> None:
    """A docs directory in the wheel is a failure."""
    wheel = tmp_path / "nepdate_core-0.1.0-py3-none-any.whl"
    _wheel(wheel, "0.1.0", ("docs/index.md",))
    assert any(
        "forbidden path" in error for error in rehearsal.check_wheel(wheel, "nepdate", "0.1.0")
    )


def test_wheel_version_mismatch_fails(rehearsal: Any, tmp_path: Path) -> None:
    """METADATA must name the version being released."""
    wheel = tmp_path / "nepdate_core-0.1.0-py3-none-any.whl"
    _wheel(wheel, "0.0.9")
    assert any(
        "METADATA version" in error for error in rehearsal.check_wheel(wheel, "nepdate", "0.1.0")
    )


def test_sdist_requires_licence_and_shared_data(rehearsal: Any, tmp_path: Path) -> None:
    """A minimal sdist fails on every required path; a complete one passes."""
    empty = tmp_path / "empty.tar.gz"
    _sdist(empty, ("nepdate_core-0.1.0/README.md",))
    errors = rehearsal.check_sdist(empty, rehearsal.CORE_SDIST)
    assert len(errors) == len(rehearsal.CORE_SDIST)
    full = tmp_path / "full.tar.gz"
    _sdist(
        full,
        (
            "nepdate_core-0.1.0/LICENSE",
            "nepdate_core-0.1.0/shared/data/NOTICE",
            "nepdate_core-0.1.0/shared/data/calendar/bs-calendar.json",
        ),
    )
    assert rehearsal.check_sdist(full, rehearsal.CORE_SDIST) == []


def test_versions_must_match_the_changelog(rehearsal: Any, tmp_path: Path) -> None:
    """The pyproject, changelog and optional init literal agree."""
    _release(tmp_path)
    assert rehearsal.check_versions("0.1.0", tmp_path) == []
    assert any("## [0.2.0]" in error for error in rehearsal.check_versions("0.2.0", tmp_path))


def test_init_version_literal_must_match(rehearsal: Any, tmp_path: Path) -> None:
    """A stale ``__version__`` literal is caught even when the pyprojects agree."""
    _release(tmp_path, literal="0.0.9")
    errors = rehearsal.check_versions("0.1.0", tmp_path)
    assert any("__version__" in error for error in errors)


def test_pyproject_versions_must_match(rehearsal: Any, tmp_path: Path) -> None:
    """A patro version different from the core is an error before the build."""
    _release(tmp_path)
    patro = tmp_path / "packages" / "nepdate-patro" / "pyproject.toml"
    patro.write_text('[project]\nname = "nepdate-patro"\nversion = "0.0.9"\n', encoding="utf-8")
    with pytest.raises(rehearsal.RehearsalError):
        rehearsal.project_version(tmp_path)


def test_twine_failure_is_reported(rehearsal: Any, tmp_path: Path) -> None:
    """A non-zero twine check becomes a release error with the tool's tail."""
    files = [tmp_path / "a.whl"]
    result = subprocess.CompletedProcess([], 1, "", "invalid wheel metadata")
    errors = rehearsal.twine_check(files, tmp_path, lambda _files, _root: result)
    assert len(errors) == 1
    assert "twine check failed" in errors[0]
    assert "invalid wheel metadata" in errors[0]


def test_stage_adds_the_patro_source_data(rehearsal: Any, tmp_path: Path) -> None:
    """The staged build carries the patro JSON beside the package, not only the generated table."""
    root = tmp_path / "repo"
    (root / "src" / "nepdate").mkdir(parents=True)
    (root / "src" / "nepdate" / "__init__.py").write_text("", encoding="utf-8")
    patro = root / "packages" / "nepdate-patro"
    (patro / "src" / "nepdate_patro").mkdir(parents=True)
    (patro / "src" / "nepdate_patro" / "__init__.py").write_text("", encoding="utf-8")
    (patro / "pyproject.toml").write_text(
        '[tool.uv.build-backend]\nmodule-name = "nepdate_patro"\n', encoding="utf-8"
    )
    for name in ("pyproject.toml", "uv.lock", "README.md", "LICENSE", "CHANGELOG.md"):
        (root / name).write_text("", encoding="utf-8")
    data = root / "shared" / "data" / "patro"
    data.mkdir(parents=True)
    (data / "2081.json").write_text("{}", encoding="utf-8")
    (root / "shared" / "data" / "calendar").mkdir()
    stage = tmp_path / "stage"
    stage.mkdir()
    rehearsal._stage_text(root, stage)
    staged = stage / "packages" / "nepdate-patro" / "shared" / "data" / "patro" / "2081.json"
    assert staged.read_text(encoding="utf-8") == "{}"
    pyproject = (stage / "packages" / "nepdate-patro" / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert 'source-include = ["shared/data/patro/**"]' in pyproject

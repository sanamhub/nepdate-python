"""Release checks run on temporary copies of the two pyprojects and the changelog."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

from nepdate import NepaliDate


def _write(root: Path, name: str, text: str) -> None:
    """Write one file below ``root``.

    Args:
        root: The temporary repository root.
        name: The relative file name.
        text: The file content.
    """
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _release(  # noqa: PLR0913 - fixtures mirror the three files release_check reads
    ci: Any,
    root: Path,
    *,
    core_version: str = "0.1.0",
    patro_version: str = "0.1.0",
    dependency: str | None = None,
    changelog: str | None = None,
) -> None:
    """Create the three files ``release_check`` reads.

    Args:
        ci: The loaded ``scripts/ci.py`` module; it owns the real names.
        root: The temporary repository root.
        core_version: The core pyproject version.
        patro_version: The patro pyproject version.
        dependency: The patro dependency on the core; the same-minor range when None.
        changelog: The changelog text; a default dated section when None.
    """
    if dependency is None:
        dependency = f"{ci.CORE_DIST}>=0.1,<0.2"
    _write(
        root,
        "pyproject.toml",
        f'[project]\nname = "{ci.CORE_DIST}"\nversion = "{core_version}"\n',
    )
    _write(
        root,
        "packages/nepdate-patro/pyproject.toml",
        f'[project]\nname = "{ci.PATRO_DIST}"\n'
        f'version = "{patro_version}"\ndependencies = ["{dependency}"]\n',
    )
    if changelog is None:
        changelog = "# Changelog\n\n## [0.1.0] - 2026-10-18\n\n### Added\n\n- The release.\n"
    _write(root, "CHANGELOG.md", changelog)


def test_release_check_passes(ci: Any, tmp_path: Path) -> None:
    """Matching versions, the same-minor range and a dated section pass."""
    _release(ci, tmp_path)
    assert ci.release_check("0.1.0", tmp_path, data=False) == []


def test_core_version_mismatch_fails(ci: Any, tmp_path: Path) -> None:
    """A core version that differs from the tag fails."""
    _release(ci, tmp_path, core_version="0.0.9")
    errors = ci.release_check("0.1.0", tmp_path, data=False)
    assert any("core pyproject version" in error for error in errors)


def test_patro_version_mismatch_fails(ci: Any, tmp_path: Path) -> None:
    """A patro version that differs from the tag fails."""
    _release(ci, tmp_path, patro_version="0.0.9")
    errors = ci.release_check("0.1.0", tmp_path, data=False)
    assert any("patro pyproject version" in error for error in errors)


def test_wrong_patro_range_fails(ci: Any, tmp_path: Path) -> None:
    """A dependency range outside the released minor fails."""
    _release(ci, tmp_path, dependency=f"{ci.CORE_DIST}>=0.1,<0.3")
    errors = ci.release_check("0.1.0", tmp_path, data=False)
    assert any("patro requires" in error for error in errors)


def test_mismatched_dependency_name_fails(ci: Any, tmp_path: Path) -> None:
    """A patro dependency on the import name, not the distribution, fails.

    A partial rename leaves the patro pointing at
    ``nepdate`` while the core is built as ``nepdate-core``.
    """
    _release(ci, tmp_path, dependency=f"{ci.CORE_MODULE}>=0.1,<0.2")
    errors = ci.release_check("0.1.0", tmp_path, data=False)
    assert any("patro requires" in error for error in errors)


def test_release_check_passes_with_empty_unreleased(ci: Any, tmp_path: Path) -> None:
    """An empty [Unreleased] section is ready for a release."""
    _release(
        ci,
        tmp_path,
        changelog=(
            "# Changelog\n\n## [Unreleased]\n\n## [0.1.0] - 2026-10-18\n\n"
            "### Added\n\n- The release.\n"
        ),
    )
    assert ci.release_check("0.1.0", tmp_path, data=False) == []


def test_release_check_rejects_unreleased_entries(ci: Any, tmp_path: Path) -> None:
    """A release fails while [Unreleased] still holds an entry."""
    _release(
        ci,
        tmp_path,
        changelog=(
            "# Changelog\n\n## [Unreleased]\n\n### Changed\n\n- The rename.\n\n"
            "## [0.1.0] - 2026-10-18\n\n### Added\n\n- The release.\n"
        ),
    )
    errors = ci.release_check("0.1.0", tmp_path, data=False)
    assert any("[Unreleased]" in error for error in errors)


def test_missing_changelog_section_fails(ci: Any, tmp_path: Path) -> None:
    """A release without its dated changelog section fails."""
    _release(ci, tmp_path, changelog="# Changelog\n\n## [Unreleased]\n")
    errors = ci.release_check("0.1.0", tmp_path, data=False)
    assert any("no '## [0.1.0]" in error for error in errors)


def test_invalid_changelog_date_fails(ci: Any, tmp_path: Path) -> None:
    """The date must be a real ISO date, not a shaped string."""
    _release(ci, tmp_path, changelog="# Changelog\n\n## [0.1.0] - 2026-13-01\n")
    errors = ci.release_check("0.1.0", tmp_path, data=False)
    assert any("invalid date" in error for error in errors)


def test_bad_semver_fails(ci: Any, tmp_path: Path) -> None:
    """The version check rejects leading zeros and missing parts."""
    _release(ci, tmp_path)
    assert ci.release_check("0.01.0", tmp_path, data=False) != []
    assert ci.release_check("1.0", tmp_path, data=False) != []
    assert ci.release_check("0.1.0b1", tmp_path, data=False) != []  # the PyPI spelling, not a tag
    assert ci.release_check("0.1.0-dev.1", tmp_path, data=False) != []


BETA_CHANGELOG = "# Changelog\n\n## [Unreleased]\n\n## [0.1.0-beta.1] - 2026-10-21\n\n- Beta.\n"


def _beta(ci: Any, root: Path, **overrides: str) -> None:
    """Create a consistent 0.1.0-beta.1 release, with optional overrides.

    Args:
        ci: The loaded ``scripts/ci.py`` module.
        root: The temporary repository root.
        **overrides: Fields passed on to ``_release``.
    """
    fields = {
        "core_version": "0.1.0b1",
        "patro_version": "0.1.0b1",
        "dependency": f"{ci.CORE_DIST}>=0.1.0b1,<0.2",
        "changelog": BETA_CHANGELOG,
    }
    fields.update(overrides)
    _release(ci, root, **fields)


def test_beta_release_check_passes(ci: Any, tmp_path: Path) -> None:
    """The tag version is semver, the pyprojects carry its PEP 440 form."""
    _beta(ci, tmp_path)
    assert ci.release_check("0.1.0-beta.1", tmp_path, data=False) == []


def test_beta_pyproject_in_semver_spelling_fails(ci: Any, tmp_path: Path) -> None:
    """A pyproject that copies the tag spelling instead of 0.1.0b1 is reported."""
    _beta(ci, tmp_path, core_version="0.1.0-beta.1")
    errors = ci.release_check("0.1.0-beta.1", tmp_path, data=False)
    assert any("expected '0.1.0b1'" in error for error in errors)


def test_beta_with_the_stable_range_fails(ci: Any, tmp_path: Path) -> None:
    """A beta patro that requires >=0.1 could not install the beta core, so it is refused."""
    _beta(ci, tmp_path, dependency=f"{ci.CORE_DIST}>=0.1,<0.2")
    errors = ci.release_check("0.1.0-beta.1", tmp_path, data=False)
    assert any("patro requires" in error for error in errors)


def test_beta_and_stable_sections_are_not_interchangeable(ci: Any, tmp_path: Path) -> None:
    """The stable tag does not pass on the beta's section, nor the beta on a stable one."""
    _release(ci, tmp_path, changelog=BETA_CHANGELOG)
    assert any(
        "no '## [0.1.0]" in error for error in ci.release_check("0.1.0", tmp_path, data=False)
    )
    _beta(ci, tmp_path, changelog="# Changelog\n\n## [0.1.0] - 2026-10-21\n\n- Stable.\n")
    errors = ci.release_check("0.1.0-beta.1", tmp_path, data=False)
    assert any("no '## [0.1.0-beta.1]" in error for error in errors)


def test_release_notes_add_install_and_verification(ci: Any, tmp_path: Path) -> None:
    """A beta's notes install with --pre and the PEP 440 version, and say how to verify."""
    _beta(ci, tmp_path)
    notes = ci.release_notes("0.1.0-beta.1", tmp_path)
    assert notes.startswith("- Beta.\n")
    assert f"pip install --pre {ci.CORE_DIST}==0.1.0b1 {ci.PATRO_DIST}==0.1.0b1" in notes
    assert "pypi-attestations verify pypi" in notes
    stable = tmp_path / "stable"
    _release(ci, stable)
    assert "--pre" not in ci.release_notes("0.1.0", stable)


def test_release_notes_extract_one_section(ci: Any, tmp_path: Path) -> None:
    """The notes stop at the next version heading."""
    _release(
        ci,
        tmp_path,
        changelog=(
            "# Changelog\n\n## [0.1.0] - 2026-10-18\n\n### Added\n\n- One.\n\n"
            "## [0.0.9] - 2026-09-01\n\n- Old.\n"
        ),
    )
    notes = ci.release_notes("0.1.0", tmp_path)
    assert "### Added" in notes
    assert "One." in notes
    assert "Old." not in notes


def test_sort_dist_splits_the_artifacts(ci: Any, tmp_path: Path) -> None:
    """Wheel and sdist names go to the distribution that owns the prefix."""
    _release(ci, tmp_path)
    dist = tmp_path / "dist"
    dist.mkdir()
    core = ci._archive_prefix(ci.CORE_DIST)
    patro = ci._archive_prefix(ci.PATRO_DIST)
    for name in (
        f"{core}0.1.0-py3-none-any.whl",
        f"{core}0.1.0.tar.gz",
        f"{patro}0.1.0-py3-none-any.whl",
        f"{patro}0.1.0.tar.gz",
    ):
        (dist / name).write_text("x", encoding="utf-8")
    ci.sort_dist(tmp_path)
    assert sorted(path.name for path in (dist / "core").iterdir()) == [
        f"{core}0.1.0-py3-none-any.whl",
        f"{core}0.1.0.tar.gz",
    ]
    assert sorted(path.name for path in (dist / "patro").iterdir()) == [
        f"{patro}0.1.0-py3-none-any.whl",
        f"{patro}0.1.0.tar.gz",
    ]


def test_sort_dist_rejects_an_unknown_artifact(ci: Any, tmp_path: Path) -> None:
    """An artifact with neither prefix is a failure, not a silent skip."""
    _release(ci, tmp_path)
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "other-0.1.0.whl").write_text("x", encoding="utf-8")
    with pytest.raises(ci.GateError):
        ci.sort_dist(tmp_path)


def test_release_check_fails_when_holidays_end_in_182_days(ci: Any, tmp_path: Path) -> None:
    """The data freshness gate is part of the release command, not a separate note."""
    _release(ci, tmp_path)
    folder = tmp_path / "shared" / "data" / "patro"
    folder.mkdir(parents=True)
    last = NepaliDate(2081, 1, 1).to_date()
    (folder / "2081.json").write_text(
        json.dumps({"days": {"2081-01-01": {"holiday": True}}}), encoding="utf-8"
    )
    at_182 = last - timedelta(days=182)
    errors = ci.release_check("0.1.0", tmp_path, today=at_182)
    assert any("public holiday" in error for error in errors)
    at_183 = last - timedelta(days=183)
    assert ci.release_check("0.1.0", tmp_path, today=at_183) == []


def test_release_check_fails_without_patro_data(ci: Any, tmp_path: Path) -> None:
    """A tree with no patro folder fails the freshness check instead of skipping it."""
    _release(ci, tmp_path)
    errors = ci.release_check("0.1.0", tmp_path)
    assert any("no patro JSON" in error for error in errors)

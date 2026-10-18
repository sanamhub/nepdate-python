"""Unit tests for ``scripts/ci.py`` helpers."""

from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path
from typing import Any

NEEDLE = "World Day Against Human Trafficking"


def _make_whl(path: Path, content: str) -> None:
    """Write a zip file named like a wheel containing one member.

    Args:
        path: The archive path.
        content: The member content.
    """
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("pkg/__init__.py", content)


def _make_targz(path: Path, content: bytes) -> None:
    """Write a gzipped tar archive containing one member.

    Args:
        path: The archive path.
        content: The member content.
    """
    with tarfile.open(path, "w:gz") as archive:
        member = tarfile.TarInfo("pkg/__init__.py")
        member.size = len(content)
        archive.addfile(member, io.BytesIO(content))


def test_archive_contains_whl(ci: Any, tmp_path: Path) -> None:
    """A wheel containing the needle reports True."""
    wheel = tmp_path / "a.whl"
    _make_whl(wheel, NEEDLE)
    assert ci._archive_contains(wheel, NEEDLE)


def test_archive_not_contains_whl(ci: Any, tmp_path: Path) -> None:
    """A wheel without the needle reports False."""
    wheel = tmp_path / "b.whl"
    _make_whl(wheel, "nothing here")
    assert not ci._archive_contains(wheel, NEEDLE)


def test_archive_contains_targz(ci: Any, tmp_path: Path) -> None:
    """An sdist containing the needle reports True."""
    sdist = tmp_path / "a.tar.gz"
    _make_targz(sdist, NEEDLE.encode("utf-8"))
    assert ci._archive_contains(sdist, NEEDLE)


def test_archive_not_contains_targz(ci: Any, tmp_path: Path) -> None:
    """An sdist without the needle reports False."""
    sdist = tmp_path / "b.tar.gz"
    _make_targz(sdist, b"nothing here")
    assert not ci._archive_contains(sdist, NEEDLE)


def test_same_minor_range(ci: Any) -> None:
    """The patro dependency range tracks the minor version."""
    assert ci._same_minor_range("0.0.0") == f"{ci.CORE_DIST}>=0.0,<0.1"
    assert ci._same_minor_range("0.1.0") == f"{ci.CORE_DIST}>=0.1,<0.2"


def test_same_minor_specifiers(ci: Any) -> None:
    """The expected specifier set is exactly the two bounds."""
    assert ci._same_minor_specifiers("0.0.0") == {">=0.0", "<0.1"}
    assert ci._same_minor_specifiers("1.4.2") == {">=1.4", "<1.5"}


def test_requirement_specifiers_ignores_order(ci: Any) -> None:
    """The two specifiers compare as a set, so their order in METADATA does not matter."""
    first = f"Requires-Dist: {ci.CORE_DIST}>=0.0,<0.1\n"
    second = f"Requires-Dist: {ci.CORE_DIST}<0.1,>=0.0\n"
    assert ci._requirement_specifiers(first, ci.CORE_DIST) == {">=0.0", "<0.1"}
    assert ci._requirement_specifiers(second, ci.CORE_DIST) == {">=0.0", "<0.1"}


def test_requirement_specifiers_negative_control(ci: Any) -> None:
    """A wrong bound, an extra bound or no requirement does not match the expected set."""
    expected = ci._same_minor_specifiers("0.0.0")
    wrong = f"Requires-Dist: {ci.CORE_DIST}>=0.0,<0.2\n"
    extra = f"Requires-Dist: {ci.CORE_DIST}>=0.0,<0.1,!=0.0.1\n"
    missing = "Requires-Dist: other>=0.0\n"
    assert ci._requirement_specifiers(wrong, ci.CORE_DIST) != expected
    assert ci._requirement_specifiers(extra, ci.CORE_DIST) != expected
    assert ci._requirement_specifiers(missing, ci.CORE_DIST) == set()


def test_parse_importtime(ci: Any) -> None:
    """Import-time output maps module names to cumulative microseconds."""
    output = (
        "import time: self [us] | cumulative | imported package\n"
        "import time:      100 |        200 | nepdate\n"
        "import time:      300 |        500 | nepdate_patro\n"
    )
    assert ci._parse_importtime(output) == {"nepdate": 200, "nepdate_patro": 500}


def test_archive_prefix_follows_the_normalized_name(ci: Any) -> None:
    """A renamed core still finds its wheel and sdist."""
    expected = ci.CORE_DIST.lower().replace("-", "_").replace(".", "_") + "-"
    assert ci._archive_prefix(ci.CORE_DIST) == expected
    assert ci._archive_prefix("nepdate-bs") == "nepdate_bs-"
    assert ci._archive_prefix("nepdate-patro") == "nepdate_patro-"


def test_outside_flags_only_foreign_modules(ci: Any) -> None:
    """The package's own modules and the allowlist pass; anything else is reported."""
    modules = {"nepdate", "nepdate._date", "enum", "json", "nepdatex"}
    assert ci._outside(modules, "nepdate", frozenset({"enum"})) == ["json", "nepdatex"]


def test_outside_flags_the_patro_module_for_the_core(ci: Any) -> None:
    """A core import that loads ``nepdate_patro`` is a gate failure.

    This is the permanent negative control for the core/patro import check.
    """
    modules = {"nepdate", "nepdate._date", "nepdate_patro", "nepdate_patro._tables"}
    assert ci._outside(modules, "nepdate", ci.CORE_IMPORT_ALLOWED) == [
        "nepdate_patro",
        "nepdate_patro._tables",
    ]

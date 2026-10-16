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
    assert ci._same_minor_range("0.0.0") == "nepdate>=0.0,<0.1"
    assert ci._same_minor_range("0.1.0") == "nepdate>=0.1,<0.2"


def test_parse_importtime(ci: Any) -> None:
    """Import-time output maps module names to cumulative microseconds."""
    output = (
        "import time: self [us] | cumulative | imported package\n"
        "import time:      100 |        200 | nepdate\n"
        "import time:      300 |        500 | nepdate_patro\n"
    )
    assert ci._parse_importtime(output) == {"nepdate": 200, "nepdate_patro": 500}

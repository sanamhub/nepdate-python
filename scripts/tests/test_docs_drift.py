"""The README API table and the ADR index cannot drift from the public surface."""

from __future__ import annotations

import re
from pathlib import Path

import nepdate
import nepdate_patro

ROOT = Path(__file__).resolve().parents[2]
EXPORTS = tuple(sorted((*nepdate.__all__, *nepdate_patro.__all__)))
API_SECTION = re.compile(r"^## API\s*$(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
DOC_LINK = re.compile(r"\[([^\]]+)\]\(([^)]*docs/[^)]+)\)")
ADR_LINK = re.compile(r"\]\((\d{4}-[^)]+\.md)\)")
DECLARATION = re.compile(r"^(?:class|def)\s+(\w+)|^([A-Z][A-Z0-9_]*)\s*:")


def _readme_missing(readme: str) -> list[str]:
    """Return exports absent from the README API table and the docs link fallback.

    Args:
        readme: The README text.

    Returns:
        The missing names.
    """
    section = API_SECTION.search(readme)
    table = section.group(1) if section is not None else ""
    linked = {match.group(1) for match in DOC_LINK.finditer(readme)}
    return [name for name in EXPORTS if f"`{name}`" not in table and name not in linked]


def _api_names(text: str) -> set[str]:
    """Read the top-level declarations from the fenced code blocks of ``docs/API.md``.

    Args:
        text: The API documentation.

    Returns:
        The declared names.
    """
    names: set[str] = set()
    inside = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            inside = not inside
            continue
        if not inside:
            continue
        match = DECLARATION.match(line)
        if match is not None:
            names.add(match.group(1) or match.group(2))
    return names


def _adr_missing(folder: Path) -> list[str]:
    """Compare the ADR files with the rows in their README.

    Args:
        folder: The ``docs/adr`` directory.

    Returns:
        One message per missing or stale row.
    """
    readme = folder / "README.md"
    if not readme.is_file():
        return [f"{readme} is missing"]
    files = {path.name for path in folder.glob("*.md") if path.name != "README.md"}
    rows = set(ADR_LINK.findall(readme.read_text(encoding="utf-8")))
    return [
        *(f"ADR README has no row for {name}" for name in sorted(files - rows)),
        *(f"ADR README row points at missing {name}" for name in sorted(rows - files)),
    ]


def problems(root: Path = ROOT) -> list[str]:
    """Return every docs drift problem below ``root``.

    Args:
        root: The repository root.

    Returns:
        One message per missing name or ADR row.
    """
    readme = root / "README.md"
    api = root / "docs" / "API.md"
    if not readme.is_file() or not api.is_file():
        return ["README.md or docs/API.md is missing"]
    found = [
        f"README API table or docs link is missing {name}"
        for name in _readme_missing(readme.read_text(encoding="utf-8"))
    ]
    documented = _api_names(api.read_text(encoding="utf-8"))
    found.extend(
        f"docs/API.md does not declare {name}" for name in EXPORTS if name not in documented
    )
    found.extend(_adr_missing(root / "docs" / "adr"))
    return found


def test_committed_docs_have_no_drift() -> None:
    """The README table and the ADR index match the committed surface."""
    assert problems(ROOT) == []


def test_a_missing_readme_name_is_reported() -> None:
    """One exported name removed from the README fails."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    missing = readme.replace("`NepaliDate`, ", "", 1)
    assert "README API table or docs link is missing NepaliDate" in problems_for_text(missing)


def problems_for_text(readme: str) -> list[str]:
    """Run the README check against one text without touching the repository.

    Args:
        readme: The README text.

    Returns:
        The missing-name messages.
    """
    return [f"README API table or docs link is missing {name}" for name in _readme_missing(readme)]


def test_a_docs_link_is_an_accepted_fallback() -> None:
    """A name linked to a docs page passes when the table does not carry it."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8").replace("`NepaliDate`, ", "", 1)
    readme += "\n[NepaliDate](docs/API.md)\n"
    assert "NepaliDate" not in _readme_missing(readme)


def test_a_missing_adr_row_is_reported(tmp_path: Path) -> None:
    """An ADR file without a README row is reported."""
    folder = tmp_path / "adr"
    folder.mkdir()
    (folder / "0001-test.md").write_text("# One\n", encoding="utf-8")
    (folder / "0002-extra.md").write_text("# Two\n", encoding="utf-8")
    (folder / "README.md").write_text(
        "| [0001](0001-test.md) | One | Accepted |\n", encoding="utf-8"
    )
    assert "ADR README has no row for 0002-extra.md" in _adr_missing(folder)
    with_row = folder / "README.md"
    with_row.write_text(
        "| [0001](0001-test.md) | One | Accepted |\n| [0002](0002-extra.md) | Two | Accepted |\n",
        encoding="utf-8",
    )
    assert _adr_missing(folder) == []


def test_an_api_name_must_be_declared() -> None:
    """A name missing from the API code blocks is reported."""
    text = (ROOT / "docs" / "API.md").read_text(encoding="utf-8")
    stripped = text.replace("class NepaliDate:", "class RenamedDate:", 1)
    assert "NepaliDate" not in _api_names(stripped)


def test_every_export_is_in_the_readme() -> None:
    """The positive control for the README table."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert _readme_missing(readme) == []

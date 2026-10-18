"""The probe details and the competitor table list the same rejected or differing dates."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "benchmarks" / "results" / "2026-10-18" / "probe.json"
COMPETITORS = ROOT / "docs" / "competitors.md"
DIRECTIONS = {"b1": "BS to AD", "b2": "AD to BS"}
TABLE_CELLS = 8
DATE_FIELDS = 3
QUESTIONABLE_FIRST = 2087
QUESTIONABLE_LAST = 2090


def _date(value: list[int] | None) -> str:
    """Format a probe date, or ``rejected`` for a missing result."""
    if value is None:
        return "rejected"
    return f"{value[0]:04d}-{value[1]:02d}-{value[2]:02d}"


def _table_rows() -> set[tuple[str, str, str, str, str, str]]:
    """Return the rows of the rejected-or-different table in ``docs/competitors.md``."""
    rows = set()
    for line in COMPETITORS.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) != TABLE_CELLS or cells[2] not in DIRECTIONS.values():
            continue
        package = cells[1].strip("`")
        rows.add((package, cells[2], cells[3], cells[4], cells[5], cells[6]))
    return rows


def _expected_rows(probe: dict[str, Any]) -> set[tuple[str, str, str, str, str, str]]:
    """Return the rows the probe document implies."""
    rows = set()
    for package, operations in probe.items():
        for op, direction in DIRECTIONS.items():
            for miss in operations[op]["misses"]:
                rows.add(
                    (
                        package,
                        direction,
                        _date(miss["input"]),
                        _date(miss["theirs"]),
                        _date(miss["ours"]),
                        "yes" if miss["questionable"] else "no",
                    )
                )
    return rows


def _problems(probe: dict[str, Any], rows: set[tuple[str, str, str, str, str, str]]) -> list[str]:
    """Check the counts, the miss fields and the docs table against the probe."""
    found: list[str] = []
    expected = _expected_rows(probe)
    if expected != rows:
        found.append("docs table does not match the probe details")
    for package, operations in probe.items():
        for op, data in operations.items():
            misses = data["misses"]
            rejected = sum(1 for miss in misses if miss["theirs"] is None)
            if len(misses) != 64 - data["matches"]:
                found.append(f"{package} {op}: miss count")
            if data["supported"] != 64 - rejected:
                found.append(f"{package} {op}: supported count")
            if data["agrees"] != (not misses):
                found.append(f"{package} {op}: agrees flag")
            for miss in misses:
                for field in ("input", "ours"):
                    if len(miss[field]) != DATE_FIELDS or not all(
                        isinstance(v, int) for v in miss[field]
                    ):
                        found.append(f"{package} {op}: bad {field}")
                if miss["theirs"] is not None and len(miss["theirs"]) != DATE_FIELDS:
                    found.append(f"{package} {op}: bad theirs")
                if miss["questionable"] != (
                    QUESTIONABLE_FIRST <= miss["bs_year"] <= QUESTIONABLE_LAST
                ):
                    found.append(f"{package} {op}: questionable flag")
    return found


def test_probe_details_and_docs_table_agree() -> None:
    """Every miss has input, theirs and ours, and every miss is in the docs table."""
    probe = json.loads(PROBE.read_text(encoding="utf-8"))
    assert _problems(probe, _table_rows()) == []


def test_probe_detail_negative_control() -> None:
    """Removing one miss from the probe makes the docs table mismatch."""
    probe = json.loads(PROBE.read_text(encoding="utf-8"))
    broken = copy.deepcopy(probe)
    broken["nepali-datetime"]["b1"]["misses"].pop()
    assert any("docs table" in message for message in _problems(broken, _table_rows()))

"""The mutation checker enforces the floor and the disposition table."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_GOOD = {"killed": 95, "survived": 5, "total": 100, "no_tests": 0, "timeout": 0}


def _files(
    tmp_path: Path, *, stats: dict[str, int] | None = None, names: list[str] | None = None
) -> tuple[Path, Path, Path]:
    """Write a stats file, a results file and a disposition table.

    Args:
        tmp_path: The temporary directory.
        stats: The stats object; a passing one when None.
        names: The survivor names; five when None.

    Returns:
        The three paths.
    """
    stats_path = tmp_path / "stats.json"
    stats_path.write_text(json.dumps(_GOOD if stats is None else stats), encoding="utf-8")
    if names is None:
        names = [f"nepdate._date.x__f__mutmut_{index}" for index in range(1, 6)]
    results = tmp_path / "results.txt"
    results.write_text(
        "\n".join(f"    {name}: survived" for name in names) + "\n", encoding="utf-8"
    )
    rows = "\n".join(f"| `{name}` | x | proof |" for name in names)
    equivalents = tmp_path / "equivalent.md"
    equivalents.write_text(
        f"| Mutant | Change | Proof |\n|---|---|---|\n{rows}\n", encoding="utf-8"
    )
    return stats_path, results, equivalents


def test_check_passes(ci: Any, mutation_check: Any, tmp_path: Path) -> None:
    """A run at or above the floor with every survivor listed passes."""
    stats, results, equivalents = _files(tmp_path)
    assert mutation_check.check(stats, results, equivalents) == []


def test_below_floor_is_a_failure(mutation_check: Any, tmp_path: Path) -> None:
    """The negative control: 80 % is below the 95 % floor."""
    stats, results, equivalents = _files(
        tmp_path, stats={"killed": 80, "survived": 20, "total": 100}
    )
    problems = mutation_check.check(stats, results, equivalents)
    assert any("below the floor" in problem for problem in problems)


def test_unlisted_survivor_is_a_failure(mutation_check: Any, tmp_path: Path) -> None:
    """A survivor without a disposition fails even when the score is high."""
    stats, results, equivalents = _files(tmp_path, names=["nepdate._date.x__f__mutmut_1"])
    results.write_text(
        results.read_text(encoding="utf-8") + "    nepdate._date.x__g__mutmut_1: survived\n",
        encoding="utf-8",
    )
    problems = mutation_check.check(stats, results, equivalents)
    assert any("no disposition" in problem for problem in problems)


def test_stale_disposition_is_a_failure(mutation_check: Any, tmp_path: Path) -> None:
    """A disposition for a mutant that is no longer surviving fails."""
    stats, results, equivalents = _files(tmp_path, names=["nepdate._date.x__f__mutmut_1"])
    equivalents.write_text(
        equivalents.read_text(encoding="utf-8")
        + "| `nepdate._date.x__old__mutmut_1` | x | proof |\n",
        encoding="utf-8",
    )
    problems = mutation_check.check(stats, results, equivalents)
    assert any("stale" in problem for problem in problems)


def test_duplicate_disposition_is_a_failure(mutation_check: Any, tmp_path: Path) -> None:
    """The same mutant id may not appear twice."""
    stats, results, equivalents = _files(tmp_path, names=["nepdate._date.x__f__mutmut_1"])
    equivalents.write_text(
        equivalents.read_text(encoding="utf-8")
        + "| `nepdate._date.x__f__mutmut_1` | x | proof |\n",
        encoding="utf-8",
    )
    problems = mutation_check.check(stats, results, equivalents)
    assert any("duplicate" in problem for problem in problems)


def test_malformed_stats_is_a_failure(mutation_check: Any, tmp_path: Path) -> None:
    """A stats file without the required fields is rejected."""
    stats, results, equivalents = _files(tmp_path, stats={"killed": 1})
    problems = mutation_check.check(stats, results, equivalents)
    assert any("no non-negative integer" in problem for problem in problems)


def test_non_equivalent_section_is_a_failure(mutation_check: Any, tmp_path: Path) -> None:
    """A survivor may only be disposed of as equivalent, not as covered by some test."""
    stats, results, equivalents = _files(tmp_path, names=["nepdate._date.x__f__mutmut_1"])
    equivalents.write_text(
        "## Test-covered (1)\n\n" + equivalents.read_text(encoding="utf-8"), encoding="utf-8"
    )
    problems = mutation_check.check(stats, results, equivalents)
    assert any("not allowed" in problem for problem in problems)


def test_equivalent_section_with_a_count_passes(mutation_check: Any, tmp_path: Path) -> None:
    """The real table's ``## Equivalent (n)`` heading is accepted."""
    stats, results, equivalents = _files(tmp_path)
    equivalents.write_text(
        "## Equivalent (5)\n\n" + equivalents.read_text(encoding="utf-8"), encoding="utf-8"
    )
    assert mutation_check.check(stats, results, equivalents) == []

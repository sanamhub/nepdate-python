"""Check a mutmut run against the floor and the committed survivor list."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FLOOR = 91.0
SURVIVOR_ID = re.compile(r"`((?:nepdate|nepdate_patro)[^`]*)`")
REQUIRED_FIELDS = ("killed", "survived", "total")


class CheckError(Exception):
    """Raised when the run cannot be checked."""


def _stats(path: Path) -> dict[str, int]:
    """Read the counts from a mutmut stats JSON file.

    Args:
        path: The stats file.

    Returns:
        The integer fields.

    Raises:
        CheckError: The file is missing, malformed or lacks a required field.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CheckError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise CheckError(f"{path} is not a JSON object")
    counts: dict[str, int] = {}
    for field in REQUIRED_FIELDS:
        value = data.get(field)
        if not isinstance(value, int) or value < 0:
            raise CheckError(f"{path} has no non-negative integer {field!r}")
        counts[field] = value
    return counts


def _dispositions(path: Path) -> set[str]:
    """Read every backticked survivor id from the disposition table.

    Args:
        path: The equivalent.md file.

    Returns:
        The mutant ids.

    Raises:
        CheckError: The file is missing or an id appears twice.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CheckError(f"cannot read {path}: {exc}") from exc
    ids = SURVIVOR_ID.findall(text)
    duplicates = {name for name in ids if ids.count(name) > 1}
    if duplicates:
        raise CheckError(f"duplicate disposition: {sorted(duplicates)[0]}")
    return set(ids)


def _survivors(path: Path) -> set[str]:
    """Read the surviving mutant ids from a mutmut results file.

    Args:
        path: The ``mutmut results`` output.

    Returns:
        The survivor ids.

    Raises:
        CheckError: The file is missing.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CheckError(f"cannot read {path}: {exc}") from exc
    return {
        match.group(1)
        for line in text.splitlines()
        if (match := re.match(r"\s*(\S+): survived$", line))
    }


def check(stats: Path, results: Path, equivalents: Path, floor: float = FLOOR) -> list[str]:
    """Return the problems with one mutation run.

    Args:
        stats: The mutmut stats JSON.
        results: The ``mutmut results --all`` output.
        equivalents: The disposition table.
        floor: The minimum efficacy percentage.

    Returns:
        One message per problem; an empty list means the run passes.
    """
    try:
        return _check(stats, results, equivalents, floor)
    except CheckError as exc:
        return [str(exc)]


def _check(stats: Path, results: Path, equivalents: Path, floor: float) -> list[str]:
    """Check a run, raising CheckError for an unreadable input."""
    counts = _stats(stats)
    efficacy = 100 * counts["killed"] / max(1, counts["killed"] + counts["survived"])
    found: list[str] = []
    if efficacy < floor:
        found.append(f"efficacy {efficacy:.2f}% is below the floor {floor:.2f}%")
    disposed = _dispositions(equivalents)
    survivors = _survivors(results)
    for name in sorted(survivors - disposed):
        found.append(f"survivor has no disposition: {name}")
    for name in sorted(disposed - survivors):
        found.append(f"disposition is stale: {name}")
    return found


def main(argv: list[str] | None = None) -> int:
    """Run the check and print one summary line.

    Args:
        argv: Command line arguments. Defaults to ``sys.argv[1:]``.

    Returns:
        0 on success, 1 on a failed check, 2 on bad arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "stats", type=Path, nargs="?", default=ROOT / "mutants" / "mutmut-cicd-stats.json"
    )
    parser.add_argument("--results", type=Path, default=ROOT / "mutants" / "results.txt")
    parser.add_argument(
        "--equivalents", type=Path, default=ROOT / "docs" / "mutation" / "equivalent.md"
    )
    parser.add_argument("--floor", type=float, default=FLOOR)
    args = parser.parse_args(argv)
    try:
        problems = check(args.stats, args.results, args.equivalents, args.floor)
    except CheckError as exc:
        print(f"mutation: {exc}", file=sys.stderr)
        return 1
    if problems:
        for problem in problems:
            print(f"mutation: {problem}", file=sys.stderr)
        return 1
    counts = _stats(args.stats)
    print(
        f"mutation: {counts['killed']} killed, {counts['survived']} survived, "
        f"floor {args.floor:.2f}%, all survivors dispositioned"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

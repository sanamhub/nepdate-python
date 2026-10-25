"""Report how far the patro data reaches and fail a release with short holiday data.

The source is ``shared/data/patro/*.json``, not the generated ``_tables.py``. Public holidays are
the release blocker: fewer than 183 days left fails. Tithi and events ending that soon are
warnings, as in the hub and the Rust port. Days are counted from today's UTC
date, the same in every port, so a release near midnight gets one answer everywhere.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path

from nepdate import NepaliDate, NepDateError

ROOT = Path(__file__).resolve().parent.parent
GATE_DAYS = 183
DATA = Path("shared") / "data" / "patro"
KINDS = ("tithi", "holidays", "events")


class DataError(Exception):
    """Raised when the patro files cannot be read or a BS date cannot be converted."""


class Report:
    """The lines, warnings and failures from one data status run.

    Attributes:
        lines: One line per data kind.
        warnings: The tithi and event warnings.
        failures: The public holiday failures.
    """

    __slots__ = ("failures", "lines", "warnings")

    def __init__(self) -> None:
        """Start an empty report."""
        self.lines: list[str] = []
        self.warnings: list[str] = []
        self.failures: list[str] = []

    @property
    def ok(self) -> bool:
        """Return whether public holidays reach the gate."""
        return not self.failures


def _has(day: dict[str, object], kind: str) -> bool:
    """Return whether one patro day has the requested data.

    Args:
        day: One day's JSON object.
        kind: ``tithi``, ``holidays`` or ``events``.

    Returns:
        True when the day contributes to that kind.
    """
    if kind == "tithi":
        return "tithi" in day
    if kind == "holidays":
        return day.get("holiday") is True
    return bool(day.get("events"))


def coverage(root: Path = ROOT) -> dict[str, tuple[str, str]]:
    """Find the first and last BS date of each data kind.

    Args:
        root: The repository root.

    Returns:
        A mapping from kind to ``(first_bs, last_bs)``. A kind with no data is absent.

    Raises:
        DataError: A patro file is missing, unreadable or has no ``days`` object.
    """
    found: dict[str, list[str]] = {kind: [] for kind in KINDS}
    paths = sorted((root / DATA).glob("*.json"))
    if not paths:
        raise DataError(f"no patro JSON files under {root / DATA}")
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DataError(f"cannot read {path}: {exc}") from exc
        days = data.get("days") if isinstance(data, dict) else None
        if not isinstance(days, dict):
            raise DataError(f"{path}: no days object")
        for key, day in days.items():
            if not isinstance(day, dict):
                raise DataError(f"{path}: {key} is not an object")
            for kind in KINDS:
                if _has(day, kind):
                    found[kind].append(key)
    return {kind: (min(keys), max(keys)) for kind, keys in found.items() if keys}


def _ad(bs: str) -> date:
    """Convert one BS date to an AD date.

    Args:
        bs: A ``YYYY-MM-DD`` BS date.

    Returns:
        The Gregorian date.

    Raises:
        DataError: The BS date is not valid.
    """
    try:
        return NepaliDate.parse(bs).to_date()
    except NepDateError as exc:
        raise DataError(f"invalid patro date {bs}: {exc}") from exc


def diagnose(root: Path = ROOT, today: date | None = None) -> Report:
    """Build the status report for one day.

    Args:
        root: The repository root.
        today: The AD date to count from; today's UTC date when None.

    Returns:
        The report with all lines, warnings and failures.

    Raises:
        DataError: The data cannot be read.
    """
    day = today or datetime.now(UTC).date()
    ranges = coverage(root)
    report = Report()
    for kind in KINDS:
        if kind not in ranges:
            report.lines.append(f"{kind:<9} no data")
            if kind == "holidays":
                report.failures.append("public holiday data is missing")
            else:
                report.warnings.append(f"{kind} data is missing")
            continue
        first, last = ranges[kind]
        first_ad = _ad(first)
        last_ad = _ad(last)
        left = (last_ad - day).days
        report.lines.append(
            f"{kind:<9} BS {first} to {last} (AD {first_ad} to {last_ad}), {left} days left"
        )
        if left < GATE_DAYS:
            message = f"{kind} data ends on BS {last} (AD {last_ad}), {left} days left"
            if kind == "holidays":
                report.failures.append(
                    f"public holiday data ends within {GATE_DAYS} days: {message}"
                )
            else:
                report.warnings.append(message)
    return report


def _iso_date(text: str) -> date:
    """Parse a ``--today`` argument.

    Args:
        text: The AD date in ``YYYY-MM-DD`` form.

    Returns:
        The parsed date.

    Raises:
        argparse.ArgumentTypeError: The text is not a real ISO date.
    """
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not an AD date in YYYY-MM-DD: {text!r}") from exc


def main(argv: list[str] | None = None) -> int:
    """Print the data status and return the release gate result.

    Args:
        argv: The arguments; ``sys.argv[1:]`` by default.

    Returns:
        0 when public holidays reach the gate, 1 when they do not, 2 on bad arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--today",
        type=_iso_date,
        default=None,
        help="AD date to count from (default: today in UTC)",
    )
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root (for tests)")
    args = parser.parse_args(argv)
    try:
        report = diagnose(args.root, args.today)
    except DataError as exc:
        print(f"data: {exc}", file=sys.stderr)
        return 1
    for line in report.lines:
        print(line)
    for warning in report.warnings:
        print(f"WARNING: {warning}")
    for failure in report.failures:
        print(f"FAIL: {failure}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

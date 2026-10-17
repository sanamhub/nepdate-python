"""Measure the bytes retained per result, with tracemalloc.

This is not the .NET Allocated measure: it is the heap still held after 10,000 calls whose
results are kept in a list. Run one operation per process so the snapshots do not overlap:

    uv run --group bench python benchmarks/bytes.py --op b1
"""

from __future__ import annotations

import gc
import json
import statistics
import sys
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from benchmarks import bench  # noqa: E402 - ROOT must be on sys.path first
from nepdate import DateRange, Lang, NepaliDate  # noqa: E402
from nepdate_patro import info  # noqa: E402

CALLS = 10_000
ARG_COUNT = 2


def _one(op: str, index: int) -> object:
    """Run one call of an operation on one input.

    Args:
        op: ``b1`` through ``b8``.
        index: The input index; it wraps around the 64 inputs.

    Returns:
        The result that the list retains.
    """
    position = index % 64
    if op == "b1":
        y, m, d = bench.DATES_BS[position]
        result: object = NepaliDate(y, m, d).to_date()
    elif op == "b2":
        result = NepaliDate.from_date(bench.DATES_AD[position])
    elif op == "b3":
        result = bench._DATES[position].add_days(1000)
    elif op == "b4":
        result = bench._DATES[position].add_months(13)
    elif op == "b5":
        result = bench._DATES[position].long(weekday=True, lang=Lang.NE)
    elif op == "b6":
        result = NepaliDate.parse(bench.DATES_TEXT[position])
    else:
        patro_date = bench._PATRO_DATES[position]
        if op == "b7":
            result = info(patro_date)
        else:
            result = [info(day) for day in DateRange.month(patro_date.year, patro_date.month)]
    return result


def measure(op: str) -> dict[str, float | int]:
    """Measure the retained bytes per result for one operation.

    Args:
        op: ``b1`` through ``b8``.

    Returns:
        The operation, the call count, the bytes per call and the median of five repeats.
    """
    samples = []
    for _ in range(5):
        _one(op, 0)
        gc.collect()
        tracemalloc.start()
        base = tracemalloc.take_snapshot()
        results = [_one(op, index) for index in range(CALLS)]
        snapshot = tracemalloc.take_snapshot()
        tracemalloc.stop()
        retained = sum(stat.size_diff for stat in snapshot.compare_to(base, "filename"))
        samples.append(retained / CALLS)
        del results
    return {"op": op, "calls": CALLS, "bytes": round(statistics.median(samples), 1)}


def main(argv: list[str] | None = None) -> int:
    """Measure one operation and print JSON.

    Args:
        argv: ``--op b1`` through ``--op b8``. Defaults to ``sys.argv[1:]``.

    Returns:
        0 on success, 2 on an unknown operation.
    """
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) != ARG_COUNT or argv[0] != "--op" or argv[1] not in {f"b{i}" for i in range(1, 9)}:
        print("bytes: expected --op b1..b8", file=sys.stderr)
        return 2
    print(json.dumps(measure(argv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

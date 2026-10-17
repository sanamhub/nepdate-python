"""Run the BENCHMARK.md operations for this port and the Python competitors.

Every benchmark function walks its inputs once and returns the list of results. pyperf runs that
function many times and divides by ``inner_loops``, the number of inputs, so the reported time is
per single operation. Competitors that reject some of the 64 dates are timed only on the dates
they accept; the ``probe`` function returns those counts and whether the results agree.
"""

from __future__ import annotations

import json
import os
import sys

import bikram
import bikram_sambat
import nepali_datetime
import nepkit
import npdatetime
import pyBSDate
import pyperf
from nepali.date_converter import converter
from nepali_calendar_utils import NepaliDateConverter

try:
    from .inputs import DATES_AD, DATES_BS, DATES_PATRO, DATES_TEXT
except ImportError:  # running as `python benchmarks/bench.py`, not as a package
    from inputs import DATES_AD, DATES_BS, DATES_PATRO, DATES_TEXT

from nepdate import DateRange, Lang, NepaliDate
from nepdate_patro import info

INPUT_COUNT = 64
PACKAGES = (
    "nepali-datetime",
    "npdatetime",
    "nepali",
    "bikram-sambat",
    "bikram",
    "pyBSDate",
    "nepali-calendar-utils",
    "nepkit",
)
_DATES = tuple(NepaliDate(y, m, d) for y, m, d in DATES_BS)
_PATRO_DATES = tuple(NepaliDate(y, m, d) for y, m, d in DATES_PATRO)


def _date_tuple(value: object) -> tuple[int, int, int]:
    """Normalise a datetime-like result to ``(year, month, day)``.

    Args:
        value: A ``datetime.date`` or an object with those three attributes.

    Returns:
        The three fields as a tuple.
    """
    return (value.year, value.month, value.day)  # type: ignore[attr-defined]


def _b1_nepali_datetime(index: int) -> tuple[int, int, int]:
    y, m, d = DATES_BS[index]
    return _date_tuple(nepali_datetime.date(y, m, d).to_datetime_date())


def _b2_nepali_datetime(index: int) -> tuple[int, int, int]:
    return _date_tuple(nepali_datetime.date.from_datetime_date(DATES_AD[index]))


def _b1_npdatetime(index: int) -> tuple[int, int, int]:
    y, m, d = DATES_BS[index]
    return npdatetime.NepaliDate(y, m, d).to_gregorian()


def _b2_npdatetime(index: int) -> tuple[int, int, int]:
    ad = DATES_AD[index]
    value = npdatetime.NepaliDate.from_gregorian(ad.year, ad.month, ad.day)
    return (value.year, value.month, value.day)


def _b1_nepali(index: int) -> tuple[int, int, int]:
    y, m, d = DATES_BS[index]
    return converter.nepali_to_english(y, m, d)


def _b2_nepali(index: int) -> tuple[int, int, int]:
    ad = DATES_AD[index]
    return converter.english_to_nepali(ad.year, ad.month, ad.day)


def _b1_bikram_sambat(index: int) -> tuple[int, int, int]:
    y, m, d = DATES_BS[index]
    return _date_tuple(bikram_sambat.conversion.bs_to_ad(y, m, d))


def _b2_bikram_sambat(index: int) -> tuple[int, int, int]:
    return bikram_sambat.conversion.ad_to_bs(DATES_AD[index])


def _b1_bikram(index: int) -> tuple[int, int, int]:
    y, m, d = DATES_BS[index]
    return _date_tuple(bikram.convert_bs_to_ad(bikram.samwat(y, m, d)))


def _b2_bikram(index: int) -> tuple[int, int, int]:
    return _date_tuple(bikram.convert_ad_to_bs(DATES_AD[index]))


def _b1_pybsdate(index: int) -> tuple[int, int, int]:
    y, m, d = DATES_BS[index]
    return pyBSDate.convert_BS_to_AD(y, m, d)


def _b2_pybsdate(index: int) -> tuple[int, int, int]:
    ad = DATES_AD[index]
    return pyBSDate.convert_AD_to_BS(ad.year, ad.month, ad.day)


def _b1_nepali_calendar_utils(index: int) -> tuple[int, int, int]:
    y, m, d = DATES_BS[index]
    value = NepaliDateConverter.convert_nepali_to_english(y, m, d)
    return (value.year, value.month, value.day_of_month)


def _b2_nepali_calendar_utils(index: int) -> tuple[int, int, int]:
    ad = DATES_AD[index]
    value = NepaliDateConverter.convert_english_to_nepali(ad.year, ad.month, ad.day)
    return (value.year, value.month, value.day_of_month)


def _b1_nepkit(index: int) -> tuple[int, int, int]:
    y, m, d = DATES_BS[index]
    return _date_tuple(nepkit.bs_to_ad(nepkit.BSDate(y, m, d)))


def _b2_nepkit(index: int) -> tuple[int, int, int]:
    return _date_tuple(nepkit.ad_to_bs(DATES_AD[index]))


_CALL = {
    ("nepali-datetime", "b1"): _b1_nepali_datetime,
    ("nepali-datetime", "b2"): _b2_nepali_datetime,
    ("npdatetime", "b1"): _b1_npdatetime,
    ("npdatetime", "b2"): _b2_npdatetime,
    ("nepali", "b1"): _b1_nepali,
    ("nepali", "b2"): _b2_nepali,
    ("bikram-sambat", "b1"): _b1_bikram_sambat,
    ("bikram-sambat", "b2"): _b2_bikram_sambat,
    ("bikram", "b1"): _b1_bikram,
    ("bikram", "b2"): _b2_bikram,
    ("pyBSDate", "b1"): _b1_pybsdate,
    ("pyBSDate", "b2"): _b2_pybsdate,
    ("nepali-calendar-utils", "b1"): _b1_nepali_calendar_utils,
    ("nepali-calendar-utils", "b2"): _b2_nepali_calendar_utils,
    ("nepkit", "b1"): _b1_nepkit,
    ("nepkit", "b2"): _b2_nepkit,
}


def _supported(package: str, op: str) -> tuple[int, ...]:
    """Return the input indexes a competitor accepts without raising.

    Args:
        package: The package key in ``PACKAGES``.
        op: ``b1`` or ``b2``.

    Returns:
        The accepted indexes, in benchmark order.
    """
    func = _CALL[(package, op)]
    accepted = []
    for index in range(INPUT_COUNT):
        try:
            func(index)
        except Exception:
            continue
        accepted.append(index)
    return tuple(accepted)


_SUPPORTED = {(package, op): _supported(package, op) for package in PACKAGES for op in ("b1", "b2")}


def probe() -> dict[str, dict[str, dict[str, int | bool]]]:
    """Return how many dates each competitor handles and whether all results agree.

    Returns:
        ``{package: {"b1": {"supported": n, "matches": m, "agrees": bool}, ...}}``.
    """
    expected = {
        "b1": tuple((ad.year, ad.month, ad.day) for ad in DATES_AD),
        "b2": DATES_BS,
    }
    report: dict[str, dict[str, dict[str, int | bool]]] = {}
    for package in PACKAGES:
        report[package] = {}
        for op in ("b1", "b2"):
            func = _CALL[(package, op)]
            supported = _SUPPORTED[(package, op)]
            matches = 0
            for index in supported:
                if func(index) == expected[op][index]:
                    matches += 1
            report[package][op] = {
                "supported": len(supported),
                "matches": matches,
                "agrees": len(supported) == INPUT_COUNT and matches == INPUT_COUNT,
            }
    return report


def _run_competitor(package: str, op: str) -> list[tuple[int, int, int]]:
    """Run one competitor operation over the dates it accepts.

    Args:
        package: The package key in ``PACKAGES``.
        op: ``b1`` or ``b2``.

    Returns:
        The normalised results, one per accepted input.
    """
    func = _CALL[(package, op)]
    return [func(index) for index in _SUPPORTED[(package, op)]]


def _run_ours(op: str) -> list[object]:
    """Run one core or patro operation over its 64 inputs.

    Args:
        op: ``b1`` through ``b8``.

    Returns:
        The results, one per input. The list keeps the work from being dropped.
    """
    if op == "b1":
        result: list[object] = [NepaliDate(y, m, d).to_date() for y, m, d in DATES_BS]
    elif op == "b2":
        result = [NepaliDate.from_date(ad) for ad in DATES_AD]
    elif op == "b3":
        result = [d.add_days(1000) for d in _DATES]
    elif op == "b4":
        result = [d.add_months(13) for d in _DATES]
    elif op == "b5":
        result = [d.long(weekday=True, lang=Lang.NE) for d in _DATES]
    elif op == "b6":
        result = [NepaliDate.parse(text) for text in DATES_TEXT]
    elif op == "b7":
        result = [info(d) for d in _PATRO_DATES]
    else:
        result = [[info(x) for x in DateRange.month(d.year, d.month)] for d in _PATRO_DATES]
    return result


_OPS = tuple(f"b{i}" for i in range(1, 9))
_KEYS = _OPS + tuple(f"{op}:{package}" for op in ("b1", "b2") for package in PACKAGES)


def _add(runner: pyperf.Runner, key: str) -> None:
    """Add one benchmark to a pyperf runner.

    Args:
        runner: The pyperf runner.
        key: ``b1`` for this port or ``b1:<package>`` for a competitor.
    """
    if ":" not in key:
        runner.bench_func(f"{key} nepdate", _run_ours, key, inner_loops=64)
        return
    op, package = key.split(":", 1)
    inner_loops = len(_SUPPORTED[(package, op)])
    if inner_loops == 0:
        print(f"bench: {package} has no {op} inputs", file=sys.stderr)
        return
    runner.bench_func(f"{op} {package}", _run_competitor, package, op, inner_loops=inner_loops)


def main(argv: list[str] | None = None) -> int:
    """Run the requested pyperf benchmarks.

    Args:
        argv: Command line arguments. Defaults to ``sys.argv[1:]``. ``--only KEY`` runs one
            benchmark; anything else is passed to pyperf, for example ``-o results.json``.

    Returns:
        0 on success, 2 on an unknown ``--only`` key.
    """
    if argv is None:
        argv = sys.argv[1:]
    # pyperf re-runs this script in every worker without the parent's arguments. The environment
    # is inherited, so it carries the single benchmark key into the workers.
    only = os.environ.get("BENCH_ONLY")
    if "--only" in argv:
        position = argv.index("--only")
        try:
            only = argv[position + 1]
        except IndexError:
            print("bench: --only needs a key", file=sys.stderr)
            return 2
        del argv[position : position + 2]
        os.environ["BENCH_ONLY"] = only
    if only is not None and only not in _KEYS:
        print(f"bench: unknown key {only}", file=sys.stderr)
        return 2
    if "--probe" in argv:
        argv.remove("--probe")
        print(json.dumps(probe(), indent=2))
        return 0
    if only is not None:
        os.environ["BENCH_ONLY"] = only
    # pyperf builds a small environment for workers, so the key needs --inherit-environ.
    # CPU 2 is the reference machine's performance core (BENCHMARK.md §1).
    argv = ["--affinity", "2", *argv]
    if only is not None:
        argv = ["--inherit-environ", "BENCH_ONLY", *argv]
    sys.argv = [sys.argv[0], *argv]
    runner = pyperf.Runner()
    for key in [only] if only else _KEYS:
        _add(runner, key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

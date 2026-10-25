# ADR-0002: Representation, tables and performance (pure Python)

- Status: Accepted
- Date: 2026-09-25 (rewritten 2026-10-08 with measured numbers, hub ADR-0004 and `BENCHMARK.md`)
- Deciders: Sanam Pakuwal

## Context

Performance is the first priority of the NepDate family (hub `BENCHMARK.md` §6). For Python the
target is: the fastest pure-Python option among the packages in `docs/competitors.md` that agree
with `shared/data`. C# NepDate (B1 13.29 ns, B2 18.64 ns on .NET 10, hub
`docs/benchmarks/dotnet.md`) is the reference column, not a target a CPython library can reach.

In CPython the cost of a conversion is interpreter work: the call, argument checks, attribute
stores and creating the result object. The table lookup itself is cheap. So the design question
is how few bytecodes and objects each operation needs, not which algorithm is O(1).

A native extension (Rust/PyO3) still pays 60 to 150 ns per call for argument parsing and object
creation, so it would be about 1.5 to 3 times faster, while needing a wheel per platform and per
free-threaded build and an sdist that needs Rust. `npdatetime` shows the cost: 21 wheels for only
3 platforms (Windows x64, Linux x64 glibc 2.34+, macOS arm64), no sdist, no free-threaded build.

### Measurements

Prototype code (not library code) in the session scratch folder, CPython 3.13.15 and 3.11.15 on
the reference machine of `BENCHMARK.md` §1, pinned to logical CPU 2, `timeit` minimum of 5 repeats,
over the 64 dates of `BENCHMARK.md` §2, on 2026-10-07 and 2026-10-08. Numbers are ns per operation
and include about 5 to 15 ns of loop overhead. They are design inputs; `docs/benchmarks.md`
publishes the real numbers, measured with `pyperf`.

| What | 3.13 ns/op | 3.11 ns/op |
|---|---:|---:|
| `date.fromordinal(o)` alone | 64.4 | 64.0 |
| `d.toordinal()` alone | 25.6 | 29.6 |
| `bisect_right` over 3589 month starts | 99.2 | 112.4 |
| `NepaliDate(y, m, d)`, slots `_y _m _d _o`, `type(x) is int` fast path | 364.8 | 354.3 |
| same, slots `_o` only | 338.2 | 334.4 |
| same, immutability by overriding `__setattr__` (`object.__setattr__` in `__init__`) | 640.4 | 616.0 |
| same, `tuple` subclass | 442.3 | 430.0 |
| same, `int` subclass | 408.7 | 402.2 |
| B1 `NepaliDate(y, m, d).to_date()`, chosen layout | 492.6 | 509.5 |
| B2 `from_date`, 32-day bucket table, at most 2 steps (chosen) | 388.2 | 672.4 |
| B2 `from_date`, `bisect_right` over month starts | 407.7 | 674.9 |
| B2 `from_date`, `bisect_right` + `divmod` for year and month | 457.3 | 1361.8 |
| B2 `from_date`, `bisect` over `YEAR_START` then a month walk (the old plan) | 774.6 | 982.5 |
| `.year` as a property over a slot / the slot itself | 26.9 / 12.9 | 50.4 / 14.3 |
| B3 `add_days(1000)`, bucket table | 318.2 | |
| B4 `add_months(13)`, clamp, no re-validation | 285.3 | |
| B5 long Nepali with weekday: precomputed digit strings, f-string | 186.8 | |
| B5 the same with `str.translate` per call | 746.8 | |
| B6 strict parse: `split("/")` fast path / regex fast path / full scanner | 852.9 / 940.5 / 1541.0 | |
| B7 patro info: one index into prebuilt per-day objects | 93.5 | |
| B7 build a slots object per call / a frozen dataclass per call / bisect per call | 285.1 / 571.6 / 1006.5 | |
| B8 month grid: prebuilt / bisect per day | 7538 / 37603 | |

A second run of the from-ordinal step alone (3.13, median of 5) gave bucket 266.6, bisect 302.9 and
bisect + `divmod` 356.4 ns, so the bucket table is about 12 % faster than `bisect`.

Import cost, 3.13, `marshal.loads` plus `exec` of the generated table module: 67 µs for the minimal
tables (23 KB `.pyc`) and 168 µs with the extra tables below (63 KB `.pyc`). Computing
`MONTH_START` at import from the month lengths instead costs 155 µs, so precomputed literals win.

Memory, `tracemalloc` bytes retained per object (3.13): 104.5 for the chosen `NepaliDate` (64 bytes
of object plus the ordinal `int`; year, month and day come from shared table objects), 80.3 for
slots `_o` only, 120.3 for a tuple subclass. A prebuilt B7 result retains 8.3 bytes per call
(measurement noise: `info` returns an existing object).

## Decision

1. **Pure Python.** One `py3-none-any` wheel for both distributions. No native extension in 0.1.
   If profiling later shows a need, the first option is mypyc-compiled wheels with the same
   pure-Python fallback (new ADR).
2. **`NepaliDate` is a hand-written class with `__slots__ = ("_y", "_m", "_d", "_o")`.** `_o` is the
   proleptic Gregorian ordinal of `datetime.date` (ALGORITHM serial + `ORDINAL_OFFSET` 673243), so
   `to_date()` is one `date.fromordinal(self._o)` and `to_ordinal()` returns the slot. Year, month
   and day are stored too, because reading them is far more common than building a date and a
   derived `.year` costs about 60 ns more per read. Comparisons and `__hash__` use `_o`, written out
   (no `functools.total_ordering`, no `dataclass`).
   - Read-only by properties without setters, so `d.year = 2000` raises `AttributeError`. No
     `__setattr__` override: it makes every construction about 75 % slower (640 vs 365 ns).
     The private slots are writable by convention only, as for any pure-Python class.
   - `__init__` checks `type(x) is int` for all three arguments first (one fast branch); otherwise
     it rejects `bool` and calls `operator.index`, so `float` and `bool` raise `TypeError`.
   - Every internal constructor (conversion, arithmetic, parsing after validation, ranges) uses
     `object.__new__(NepaliDate)` and stores the four slots directly, never `__init__`, so a value is
     validated once.
3. **Core tables are constants in the generated `src/nepdate/_calendar.py`**, loaded from the
   `.pyc` by `marshal`, with no work at import:
   - `MONTH_LENGTHS: bytes` (3588),
   - `MONTH_START_ORD: tuple[int, ...]` (3589 ordinals; BS to AD is one index),
   - `MONTH_YEAR: tuple[int, ...]` (3588; the BS year of month index `i`) and `MONTH_NUM: bytes`
     (3588; month 1 to 12), so AD to BS never runs `divmod`,
   - `BUCKET: tuple[int, ...]` (3413; for each 32-day block from the first ordinal, the month index
     containing its first day). A month has at least 29 days, so AD to BS is one index plus at most
     two comparisons with `MONTH_START_ORD`. The generator asserts the two-step bound for all
     109,212 days.
   - `YEAR_START` (300 serials) and `MONTH_START` (3589 serials) stay for ALGORITHM §2 parity
     checks and `DateRange.year`.
4. **Formatting tables:** precomputed tuples of the Nepali-digit strings for days 1 to 32 (padded and
   unpadded) and years 1901 to 2199, built once at import of the formatting module (about 330
   `str.translate` calls, under 0.1 ms). Long formats are one f-string over table lookups.
   `strftime` is never used.
5. **Strict parse:** a fast path for ASCII input that splits into exactly three groups of 1 to 4
   ASCII digits on one separator; anything else goes to the PARSING §1 scanner, which alone
   produces errors. The fast path must accept only inputs the scanner accepts with the same result
   (a property test checks it).
6. **Patro (`nepdate_patro`, separate distribution, ADR-0001):** the generated
   `nepdate_patro/_tables.py` holds the compact tables of PATRO §3, keyed by `datetime.date` ordinal
   (`NepaliDate.to_ordinal()`, public API only): `TITHI_FIRST` + `TITHI_INDEX: bytes` into 32 tithi
   names, sorted `HOLIDAYS`, sorted `EVENT_DAYS` with spans into `EVENT_IDS`, and deduplicated
   `NAMES`. At import, `nepdate_patro` builds from them one `DAY_INFO` tuple: one prebuilt, immutable
   `CalendarInfo` per coverage day (2793 days, 2077-01-01 to 2084-08-20), sharing `Tithi` and `Event`
   objects. PATRO §3 allows this dense layout because the benchmark above shows it is faster:
   `info(d)` is one subtraction, one range check and one tuple index (93.5 ns), returns an existing
   object and allocates nothing. The build costs about 2.4 ms (860 µs objects, 1533 µs per-day
   infos), paid only by `import nepdate_patro`.
7. **Import cost:** `import nepdate` under 5 ms and `import nepdate_patro` (with the core already
   imported) under 10 ms, both checked by ADR-0004 gate 5. `import nepdate` never loads the patro.
8. **Targets** (CPython 3.13, reference machine, measured with `pyperf`; each is the
   prototype number plus about 15 %):

   | ID | Operation | Target ns/op | Prototype ns/op | C# NepDate ns/op |
   |---|---|---:|---:|---:|
   | B1 | BS to AD | < 550 | 492.6 | 13.29 |
   | B2 | AD to BS | < 450 | 388.2 | 18.64 |
   | B3 | add 1000 days | < 400 | 318.2 | 17.50 |
   | B4 | add 13 months, clamp | < 350 | 285.3 | 18.85 |
   | B5 | long, Nepali, weekday | < 400 | 186.8 (formatter body only) | 153.02 |
   | B6 | strict parse | < 1000 | 852.9 | 21.55 |
   | B7 | patro info | < 150 | 93.5 | 47.93 |
   | B8 | patro month grid | < 9000 | 7538 | 3133 |

   And, for B1 and B2 (the operations every competitor has), faster than every package in
   `docs/competitors.md` that agrees with the data on the 64 dates (`BENCHMARK.md` §6).

## Consequences

- One wheel for every platform, Pyodide and free-threaded CPython included. Tables are immutable
  `bytes` and `tuple` objects and `DAY_INFO` is built under the import lock, so no locks are needed
  under free-threading.
- The core `_calendar.py` is about 63 KB as `.pyc`; the cost is 168 µs at import.
- CPython stays 20 to 40 times slower than C# NepDate on B1 to B4. That is the language, and the
  benchmark table says so rather than hiding it.
- `NepaliDate` private slots can be overwritten by code that reaches into `_y`; this is accepted for
  speed and documented in the class docstring.

# P1: Core types and BS ↔ AD conversion

Read first: ADR-0002 (all of it: the layout below comes from its measurements), ADR-0003,
`docs/API.md` (NepaliDate, enums, errors), `shared/spec/ALGORITHM.md` §1–7, `shared/spec/PARITY.md`.

## Tasks

### P1-01 Generated tables
Extend `scripts/codegen.py` to write the tables of ADR-0002 §3 into `src/nepdate/_calendar.py`:
`MONTH_LENGTHS` (`bytes`, 3588), `MONTH_START` (tuple of 3589 serials), `YEAR_START` (tuple of
300 serials), `ORDINAL_OFFSET` (`date(1844, 4, 11).toordinal()`, which is 673243; ordinal = serial +
`ORDINAL_OFFSET`), `MONTH_START_ORD` (tuple of 3589 ordinals), `MONTH_YEAR` (tuple of 3588 years),
`MONTH_NUM` (`bytes`, 3588, values 1 to 12) and `BUCKET` (tuple of 3413 month indexes: entry `k` is
the month index containing ordinal `MONTH_START_ORD[0] + 32 * k`). Long literals wrapped at 100
columns with a `# 1901` comment per year where the table is per month.
AC: `len(MONTH_LENGTHS) == 3588`; `len(MONTH_START) == 3589`; `len(YEAR_START) == 300`;
`YEAR_START[-1] == MONTH_START[-1] == 109212`; `ORDINAL_OFFSET == 673243`; `len(BUCKET) == 3413`;
the generator asserts, for every ordinal in range, that the month index is `BUCKET[k >> 5]` plus 0,
1 or 2 (a test feeds it a table where that fails and expects a non-zero exit); `--check` passes
after generation.

### P1-02 Enums and errors (`_names.py`, `_errors.py`)
`Lang`, `Month`, `Weekday`, `ErrorKind`, `NepDateError(ValueError)` per API.

### P1-03 `NepaliDate` construction and accessors (`_date.py`)
`__slots__ = ("_y", "_m", "_d", "_o")` (ADR-0002 §2). `__init__`: if all three arguments pass
`type(x) is int`, go straight to ALGORITHM §3; otherwise raise `TypeError` for a `bool` and convert
the rest with `operator.index` (which raises `TypeError` for `float`). Store `_o =
MONTH_START_ORD[i] + day - 1`. Properties without setters per API. `__eq__`, `__lt__`, `__le__`,
`__gt__`, `__ge__`, `__hash__` on `_o`, returning `NotImplemented` for other types. No
`__setattr__` override (ADR-0002 §2). A private module function `_from_parts(y, m, d, o)` builds a
date with `object.__new__` and is the only constructor the rest of the package uses.
AC: `NepaliDate(2081, 4, 32)` works; `NepaliDate(2081, 4, 33)` raises with
`kind is ErrorKind.INVALID_DAY`; `NepaliDate(True, 1, 1)` and `NepaliDate(2081.0, 1, 1)` raise
`TypeError`; a year given as an object with `__index__` (a small test class) works;
`NepaliDate(1900, 13, 40)` raises `OUT_OF_RANGE` and `NepaliDate(2081, 13, 40)` raises
`INVALID_MONTH` (ALGORITHM §3 precedence); `d.year = 2000` raises `AttributeError`.

### P1-04 Conversion
`to_ordinal` returns `_o`; `to_date` is `date.fromordinal(self._o)`; `from_date(d)` and
`from_ordinal(n)` use the bucket lookup of ADR-0002 §3: `k = o - MONTH_START_ORD[0]`, range check
`0 <= k < 109212`, `i = BUCKET[k >> 5]`, then at most two `if o >= MONTH_START_ORD[i + 1]: i += 1`,
then year `MONTH_YEAR[i]`, month `MONTH_NUM[i]`, day `o - MONTH_START_ORD[i] + 1`. No `bisect`, no
`divmod`, no loop. `weekday` = `self._o % 7` (Sunday = 0; the same as ALGORITHM §7's
`(s + 4) % 7`), `day_of_year`, `first_of_month`, `last_of_month`, `MIN`, `MAX`.
AC: `NepaliDate(1901, 1, 1).to_date() == date(1844, 4, 11)`;
`NepaliDate(2199, 12, 30).to_date() == date(2143, 4, 15)`; `from_date(date(1844, 4, 10))` and
`from_date(date(2143, 4, 16))` raise `NepDateError` with `kind is ErrorKind.OUT_OF_RANGE`; the
ALGORITHM §9 reference rows match (AD, and weekday where the row gives one);
`from_ordinal(673242)` and `from_ordinal(673243 + 109212)` raise `OUT_OF_RANGE`.

### P1-05 Tests
- `test_vectors.py`: `month-boundaries.csv` (7176 rows) and golden `dates.tsv` columns `ad`, `weekday`,
  `day_of_year`, `month_length`.
- `test_exhaustive.py`: every serial 0..=109211 round-trips (109,212 dates), and for each the
  bucket lookup equals `bisect_right(MONTH_START_ORD, o) - 1` (the reference). Mark it `slow` if it
  takes over 2 s; `scripts/ci.py` runs all tests including `slow`, and `pytest -m "not slow"` is
  only for quick local runs.
- `test_properties.py`: hypothesis round-trip over `st.integers(0, 109211)`.
- `test_csharp_catalog.py`: one test per catalogue row tagged phase 1 (`00-ROADMAP.md`, "C# test
  catalogue").

## Checkpoint (stop here for review)

The reviewer checks:
- [ ] `uv run python scripts/ci.py` ends with `ci: 7/7 gates passed` on a clean checkout.
- [ ] `_calendar.py` matches `scripts/codegen.py --check`; the row for BS 2081 is easy to find.
- [ ] `NepaliDate` has exactly the four slots of ADR-0002 §2 and no `__dict__`
      (`not hasattr(NepaliDate(2081, 1, 1), "__dict__")`).
- [ ] `from_date` and `from_ordinal` use `BUCKET` with at most two steps; no `bisect`, `divmod` or
      loop on the hot path; arithmetic and parsing build dates through `_from_parts`, not `__init__`.
- [ ] A quick `timeit` of B1 and B2 on the 64 dates (`BENCHMARK.md` §2) is within the ADR-0002 §8
      targets on CPython 3.13, or the PR says by how much it misses.
- [ ] `python -X importtime -c "import nepdate"` is under 5 ms.
- [ ] Every C# catalogue row tagged phase 1 has a test named after its `id` or a comment naming the
      deviation.
- [ ] Why does `__init__` check `type(x) is int` first and only then call `operator.index`? (Answer:
      speed for the common case, and `operator.index(True)` returns 1, so `bool` needs its own check.)

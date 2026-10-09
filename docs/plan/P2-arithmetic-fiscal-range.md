# P2: Arithmetic, diff, fiscal year, range

Read first: `shared/spec/ALGORITHM.md` §8–8b, `docs/API.md` (arithmetic, fiscal, range),
`shared/spec/PARITY.md` D-02, D-03, D-07, D-08, D-09.

## Tasks

### P2-01 Days
`add_days`, `days_until`, `__add__(timedelta)`, `__sub__` (date → `timedelta`, `timedelta` →
date). A `timedelta` with a fractional day raises `NepDateError` (D-03: integers only).
`add_days(n)` is `from_ordinal`'s bucket lookup on `self._o + n` (ADR-0002 §3), no re-validation.
AC: golden `add-days.tsv` (9162 rows); `MAX.add_days(1)` raises `OUT_OF_RANGE`.

### P2-02 Months and years
`add_months`, `add_years` with `Overflow.CLAMP` / `Overflow.SPILL` (ALGORITHM §8). Use `divmod` for
the month/year split, with tests for negative `n`. Clamp reads the target month's length straight
from `MONTH_LENGTHS` and builds the result with `_from_parts` (no throwaway date, no
re-validation; hub lesson 6 in `docs/research/dotnet-internals.md`).
AC: golden `add-months.tsv` (10180 rows): column `clamp` with `Overflow.CLAMP` and column
`overflow` with `Overflow.SPILL`; the §8 examples (2081-04-32 +2 months: CLAMP 2081-06-30, SPILL
2081-07-02; +5 months: CLAMP 2081-09-29, SPILL 2081-10-03); `NepaliDate(2081, 4, 15).add_months(-1)`
is 2081-03-15 and `add_months(-16)` is 2079-12-15; `MAX.add_months(1)` and `MIN.add_months(-1)`
raise `OUT_OF_RANGE`.

### P2-03 `diff` (ALGORITHM §8a)
ALGORITHM §8a has no worked examples; these were computed from `shared/data/` with the §8a
pseudocode on 2026-10-07:

| a | b | `negative, years, months, days, total_days` |
|---|---|---|
| 2081-04-15 | 2082-01-01 | `False, 0, 8, 17, 258` |
| 2082-01-01 | 2081-04-15 | `True, 0, 8, 17, -258` |
| 2081-04-32 | 2081-06-30 | `False, 0, 2, 0, 61` |
| 2081-01-01 | 2081-01-01 | `False, 0, 0, 0, 0` |
| 2000-01-01 | 2081-04-15 | `False, 81, 3, 14, 29693` |

AC: the table above; hypothesis: `a.diff(b).total_days == a.days_until(b)` and
`a.diff(b).negative == (b < a)` for any two valid dates.

### P2-04 `FiscalYear`, `Quarter` (ALGORITHM §8b)
AC: golden `dates.tsv` columns `fy_start`, `fy_end`, `quarter_start`, `quarter_end`;
`FiscalYear(2082).label(Lang.NE) == "२०८२/८३"`.

### P2-05 `DateRange`
Per API; iteration yields `NepaliDate` objects built from serials (no re-validation per step).
AC: for every year, `len(DateRange.year(y))` equals the sum of its month lengths;
`NepaliDate(2081, 4, 15) in DateRange.month(2081, 4)`.

### P2-06 C# catalogue rows
`tests/test_csharp_catalog.py`: one test per catalogue row tagged phase 2 (`00-ROADMAP.md`, "C# test
catalogue").

## Checkpoint (stop here for review)

The reviewer checks:
- [ ] `uv run python scripts/ci.py` ends with `ci: 7/7 gates passed`.
- [ ] `add_days`, `add_months`, `add_years` and range iteration build dates with `_from_parts`;
      none calls `NepaliDate.__init__` or builds a date only to read its month length.
- [ ] Negative amounts are tested for every operation (Python `//` floors where C# truncates).
- [ ] A quick `timeit` of B3 and B4 on the 64 dates is within the ADR-0002 §8 targets on CPython 3.13,
      or the PR says by how much it misses.
- [ ] `DateRange` has no set operations (D-09) and `len()` is computed, not counted by iterating.
- [ ] Every C# catalogue row tagged phase 2 has a test named after its `id` or a comment naming the
      deviation.

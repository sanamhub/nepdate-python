# P4: patro distribution and interop

Read first: `shared/spec/PATRO.md`, `docs/API.md` (`nepdate_patro`, `today`), ADR-0001 §1 and §5,
ADR-0002 §6 and §8, ADR-0003, ADR-0004 gates 5 to 7, hub ADR-0004
([`docs/adr/0004-patro-in-a-separate-package.md`](https://github.com/sanamhub/nepdate/blob/main/docs/adr/0004-patro-in-a-separate-package.md)),
`shared/spec/PORT-PLAN.md` phase 4.

All patro code goes in `packages/nepdate-patro/`. Nothing in this phase adds a file, import or
string to `src/nepdate/` except P4-03.

## Tasks

### P4-01 Patro tables (`packages/nepdate-patro/src/nepdate_patro/_tables.py`)
Extend `scripts/codegen.py` to read every `shared/data/patro/*.json` and write the tables of
ADR-0002 §6, keyed by `datetime.date` ordinal (`NepaliDate.to_ordinal()`):
- `TITHI_FIRST` (ordinal of 2078-01-02), `TITHI_INDEX: bytes` (one byte per day), `TITHI_NAMES`
  (tuple of 32 `(np, en)` pairs). Fail with a non-zero exit if a day inside the tithi range has no
  tithi.
- `HOLIDAYS`: sorted tuple of ordinals.
- `EVENT_DAYS`: sorted tuple of ordinals; `EVENT_SPANS`: per event day, the start and end offsets
  into `EVENT_IDS`; `EVENT_IDS`: indexes into `NAMES`, in file order.
- `NAMES`: deduplicated `(np, en)` pairs used by events.
- `COVERAGE_FIRST`, `COVERAGE_LAST`: ordinals of 2077-01-01 and 2084-08-20 (PATRO §2 `coverage`).

The core's `_calendar.py` is unchanged by this task.
AC (PATRO §3, counts from the data on 2026-10-07):
- `len(TITHI_INDEX) == 2190` (T), `len(TITHI_NAMES) == 32`, `len(HOLIDAYS) == 294` (H),
  `len(EVENT_DAYS) == 1671` (E), `len(EVENT_IDS) == 3032`;
- tithi and event names together have 753 distinct `(np, en)` pairs;
- a test removes the tithi of one day inside 2078-01-02..2083-12-30 from a copy of the data and
  expects the generator to exit non-zero;
- `--check` passes after generation.

### P4-02 `nepdate_patro`
`info`, `coverage`, `public_holidays`, frozen `Tithi`, `Event`, `CalendarInfo` per `docs/API.md`.
At import, build the dense `DAY_INFO` tuple of ADR-0002 §6 from `_tables.py`: 32 `Tithi` objects,
one `Event` object per used `NAMES` entry, and one `CalendarInfo` per coverage day (2793 days)
sharing them; days without data share one `EMPTY = CalendarInfo(None, False, ())`. `info(d)` is
`k = d.to_ordinal() - COVERAGE_FIRST`, then `DAY_INFO[k]` if `0 <= k < len(DAY_INFO)`, else `EMPTY`.
It builds no object per call. `info` looks a date up with `d.to_ordinal()`; it uses only the core's public API (no `_s`, no
import from `nepdate._...`). `coverage()` and `public_holidays()` build dates with
`NepaliDate.from_ordinal`.
AC:
- every row of the PATRO §4 anchor table, including the two empty dates (2070-06-15, 2090-01-01:
  `CalendarInfo(None, False, ())`);
- `coverage() == DateRange(NepaliDate(2077, 1, 1), NepaliDate(2084, 8, 20))`;
- `public_holidays()` yields 294 dates in ascending order, the first 2077-01-01 and the last
  2084-08-18;
- `info(MIN)` and `info(MAX)` return the empty `CalendarInfo` without raising;
- `Tithi("पञ्चमी", "Panchami").label(Lang.NE) == "पञ्चमी"`;
- a test in a subprocess runs `import nepdate` and checks `"nepdate_patro" not in sys.modules`;
- `info(d) is info(d)` for a date inside coverage (no object built per call), and
  `info(NepaliDate(2070, 6, 15)) is info(NepaliDate(2090, 1, 1))` (the shared `EMPTY`);
- for every day of coverage, `DAY_INFO` agrees with a slow reference lookup over the compact tables
  (bisect over `HOLIDAYS` and `EVENT_DAYS`), so the dense table can't drift from PATRO §3;
- one test per C# catalogue row tagged phase 4 (`00-ROADMAP.md`, "C# test catalogue").

### P4-03 `today(tz=None)` (core)
`datetime.now(tz or ZoneInfo("Asia/Kathmandu")).date()`, then `from_date`.
AC: with a fixed clock (inject `now` in a private helper), 2024-07-30 18:30 UTC gives 2081-04-16 in
Nepal and 2081-04-15 for `today(timezone.utc)`.

### P4-04 Core and patro stay apart (PORT-PLAN phase 4)
No new code if P0-03 was done right; this task proves the gates still hold with real event data.
AC (all through `uv run python scripts/ci.py`):
- gate 6: the core wheel `METADATA` has no `Requires-Dist` naming `nepdate-patro`; no file in the
  core wheel or sdist contains `World Day Against Human Trafficking`; the core test suite passes in a venv without
  `nepdate_patro`;
- gate 6 fails if `src/nepdate/` gets a file containing `World Day Against Human Trafficking` (check once by hand, say so in
  the PR, then remove the file);
- gate 7: the patro test suite passes in a venv with the two built wheels;
- the patro wheel `METADATA` has a `Requires-Dist` for `<core-name>` whose specifiers are exactly
  `>=0.0` and `<0.1` (the range for the current version, ADR-0001 §1; compare the set of
  specifiers, not the raw string, because their order may vary), and both wheels have the same
  version.

## Checkpoint (stop here for review)

The reviewer checks:
- [ ] `uv run python scripts/ci.py` ends with `ci: 7/7 gates passed`, including gates 5, 6 and 7.
- [ ] `src/nepdate/` has no new file, import or string from the patro, except `today` (P4-03); the
      core wheel doesn't contain `World Day Against Human Trafficking` and the patro wheel does.
- [ ] `nepdate_patro` uses only the core's public API (`grep -rn "nepdate\._" packages/` finds
      nothing).
- [ ] `info` returns prebuilt objects (the `is` tests exist); `import nepdate_patro` is under 10 ms.
- [ ] A quick `timeit` of B7 and B8 on the 64 patro dates (`BENCHMARK.md` §3) is within the ADR-0002
      §8 targets on CPython 3.13, or the PR says by how much it misses.
- [ ] Counts T = 2190, H = 294, E = 1671 and 753 distinct name pairs are asserted, and every PATRO §4
      anchor passes.
- [ ] Every C# catalogue row tagged phase 4 has a test named after its `id` or a comment naming the
      deviation.

# P5: Docs, benchmarks, release 0.1.0

Read first: ADR-0002 §8, `shared/spec/BENCHMARK.md`, ADR-0005, `docs/competitors.md`,
`shared/spec/PORT-PLAN.md` phase 5.

## Tasks

### P5-01 Docs
Google-style docstring on every public name in both packages (summary, returns, raises), with a
doctest where it helps. README quick start as doctests (run by pytest), with one conversion, one
`format` call and one `nepdate_patro.info` call under a heading that says it needs
`pip install nepdate-patro`. `packages/nepdate-patro/README.md` (its PyPI page) with its own short
example. Absolute links in both READMEs, because they are the PyPI pages.
AC: ruff rule `D` passes; every name in `__all__` of both packages has a docstring (a test walks
`__all__`); the README doctests pass in gate 3.

### P5-02 Benchmarks and competitor comparison (`benchmarks/`)
Protocol: `shared/spec/BENCHMARK.md`. Goal: ADR-0002 §8, which is BENCHMARK §6 for Python (the
fastest pure-Python option among competitors that agree with the data).
- Dependency group `bench`: `pyperf` and the eight packages in `docs/competitors.md`, pinned with
  `==`. Never in the runtime dependencies.
- `benchmarks/inputs.py`: the 64 BS dates of BENCHMARK §2 (serials `s0 + i * ((s1 - s0) // 63)`,
  BS 2000-01-01 to 2090-12-30), their AD dates, their `YYYY/MM/DD` strings, and the 64 patro dates
  of BENCHMARK §3. Computed from `_calendar.py` and also committed as literals; a test checks that
  both agree.
- `benchmarks/bench.py`: one `pyperf` benchmark per operation and library, each iteration running
  the operation over all 64 inputs and appending each result to a list that is returned (so the
  result is consumed); reported time is per single operation (`inner_loops=64`). Ours:

  | ID | Call |
  |---|---|
  | B1 | `NepaliDate(y, m, d).to_date()` |
  | B2 | `NepaliDate.from_date(ad)` |
  | B3 | `d.add_days(1000)` |
  | B4 | `d.add_months(13)` (clamp is the default) |
  | B5 | `d.long(weekday=True, lang=Lang.NE)` |
  | B6 | `NepaliDate.parse(text)` |
  | B7 | `nepdate_patro.info(d)` |
  | B8 | `[info(x) for x in DateRange.month(d.year, d.month)]` |

  Competitors: B1 and B2 with the calls in `docs/competitors.md`, inputs as ints and outputs
  normalised to `datetime.date` or `(y, m, d)`. B3 to B8 only where a package has an equivalent call;
  `benchmarks/README.md` lists each call used, and the table says `n/a` otherwise.
- Range: several competitors stop before BS 2090. A package that fails on some of the 64 dates is
  timed on the dates it supports, marked `n/64` in the table, and never ranked.
- Run, from `cmd`, on the reference machine (BENCHMARK §1), CPython 3.13, idle machine:
  `start /affinity 4 /wait uv run --group bench python benchmarks/bench.py --rigorous -o benchmarks/results/<date>.json`.
  Child processes inherit the affinity mask, so pyperf workers stay on CPU 2. `pyperf` reports mean
  and standard deviation over its worker processes; warm-up is pyperf's.
  Also run once on 3.11 and 3.14 and report those in a second, smaller table.
- Bytes column: BENCHMARK §4 lets Python say "not measured". Report instead `tracemalloc` bytes
  retained per result over 10,000 calls, labelled "retained bytes/op, not the same measure as
  .NET's Allocated".
- "Agrees" column: does the package match `shared/data/` on all 64 dates (both directions)?
- `docs/benchmarks.md`: the BENCHMARK §1 machine table, Python and package versions, the exact
  command, and the BENCHMARK §5 table (ours, bytes, each competitor with its agrees column, and C#
  NepDate copied from the hub's `docs/benchmarks/dotnet.md` .NET 10 column). Say that `npdatetime`
  is a native extension.
- If a target is missed, report it to the human with the numbers and a `cProfile` run; don't drop
  features or guess-optimise.

### P5-03 Release workflow + runbook
`.github/workflows/release.yml` per ADR-0005 and `docs/runbooks/release.md`. `scripts/ci.py
release-check X.Y.Z` per ADR-0005.
Precondition: P0-06 done (the four pending trusted publishers and both environments exist).
AC:
- `release-check` fails when the two `pyproject.toml` versions differ, when the patro dependency
  range doesn't match `X.Y`, or when `CHANGELOG.md` has no `## [X.Y.Z]` section (unit tests on
  temporary copies);
- a dry run publishes the core and then `nepdate-patro` to TestPyPI, and the install check
  (`pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/
  <core-name>==X.Y.Z nepdate-patro==X.Y.Z`) passes from there.

### P5-04 0.1.0
Set `version = "0.1.0"` in both `pyproject.toml` files, set the patro dependency to
`"<core-name>>=0.1,<0.2"`, move `[Unreleased]` to `## [0.1.0] - <date>`.
AC: `uv run python scripts/ci.py release-check 0.1.0` passes. **Agent stops here.** The human tags
and approves.

## Checkpoint (stop here for review; the human tags)

The reviewer checks:
- [ ] `uv run python scripts/ci.py` and `uv run python scripts/ci.py release-check 0.1.0` pass.
- [ ] Every name in both `__all__` has a docstring; the README doctests run in gate 3.
- [ ] `docs/benchmarks.md` has the BENCHMARK §5 table for B1 to B8 with the exact command, versions,
      the agrees column and the C# column; every ADR-0002 §8 target is met, or the miss is reported
      with numbers.
- [ ] The `bench` group is not in either package's runtime dependencies.
- [ ] The TestPyPI dry run of both distributions passed and the install check ran.
- [ ] `CHANGELOG.md` has `## [0.1.0]`; both versions are `0.1.0`; the patro depends on
      `<core-name>>=0.1,<0.2`.

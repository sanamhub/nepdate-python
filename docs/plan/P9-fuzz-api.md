# P9: Fuzzing with oracles and an API compatibility gate

Read first: ADR-0003, ADR-0004, ADR-0009 rules 7 and 8, [`docs/API.md`](../API.md), the P8
review row in [`PROGRESS.md`](PROGRESS.md), and the P8 mutation plan. P7-02 to P7-05 stay parked:
this phase does not run benchmarks or change ADR-0008, `benchmarks/` or `docs/benchmarks.md`.

P8 found that a test can execute a line and still miss the behaviour the line carries. P9 adds
two checks that do not depend on the implementation: properties with an independent oracle, and
coverage-guided fuzzing that looks for exceptions the public contract does not allow. It also
adds a committed API snapshot so a public change cannot arrive without a diff and a docs update.

## Rules for this phase

- No public API or behaviour change. `docs/api-snapshot.json` is the baseline. A finding stops the
  phase: report it first, add a failing regression test marked `xfail(strict=True)`, and do not
  continue with later tasks.
- The only production change is P9-04, removal of the private `format_pattern` argument. It must
  leave the snapshot byte-identical.
- Toolchains and caches go under `D:\devcache\p9` on Windows or `/mnt/d/devcache/p9` in WSL, never
  on C:. At most 4 jobs run at once.
- No tag, publish, remote, settings or secrets change. No AI attribution in commits or docs.
- Atheris and mutmut need Linux. Local runs use WSL Ubuntu 26.04; GitHub Actions uses
  `ubuntu-latest`.

## Existing property inventory

The public parse and format entry points and the property that guards each one before P9:

| Entry point | Existing guard | Gap |
|---|---|---|
| `NepaliDate.parse` | `tests/test_parse.py::test_arbitrary_text_raises_only_nepdate_error`; `test_fast_path_agrees_with_the_scanner` | No round trip from formatted output. |
| `NepaliDate.parse_lenient` | `tests/test_parse_lenient.py::test_arbitrary_text_raises_only_nepdate_error` | No agreement with strict parsing. |
| `NepaliDate.str` and `isoformat` | Golden `dates.tsv` columns and examples | No property. |
| `NepaliDate.short` | Golden column `dmy_dash_nopad`; every order and separator example | No property. |
| `NepaliDate.long` | Golden `long_*` columns; option examples | No property. |
| `NepaliDate.format` | Golden `format-pattern.tsv` (444 of 451 rows) and examples | No round trip, no digit-language property. |
| `NepaliDate.__format__` | Examples in `tests/test_format_pattern.py` | No property. |
| `NepaliDate.from_ordinal` and `to_ordinal` | `tests/test_properties.py::test_round_trip` compares `from_ordinal`, `to_date` and `from_date` | The oracle is `datetime.date`, but the property does not build from a `datetime.date`. |
| `NepaliDate.add_days` | `tests/test_properties.py::test_add_days_inverse` | Covered. |
| `NepaliDate.add_months` | 10,180 golden rows in `tests/test_months.py` | No property against a month-index oracle. |
| `NepaliDate.diff` | `tests/test_diff.py::test_diff_properties` | Covered. |

`format_pattern` is private. Its `weekday` argument is dead: it is passed only to `format_long`
with `with_weekday=False`, so no public output depends on it. P8 review finding 6 asks for its
removal.

## P9-00 Plan

This file, the roadmap row and the progress row, committed before any dependency or code change.
AC:
- The plan names every task from P9-00 to P9-04, the tools and versions, the local budget, the
  worker limit, the finding rule and the checkpoint report.
- The roadmap and progress tables link this file and the P9 task IDs.
- No production code or dependency changes in this task.

## P9-01 Oracle properties

Extend the suite with `tests/test_properties_format_parse.py`. Each property uses an oracle that
does not call the function under test as its own expected value.

1. **Round trip through `format`.** An explicit catalogue of every standard pattern (`""`, `G`,
   `g`, `d`, `D`, `s`) and custom patterns with a full year, exact separators, quoted literals,
   escaped tokens, padded and unpadded fields, and full or short month names. Numeric patterns
   round-trip through `parse`; month-name patterns round-trip through `parse_lenient`. The date
   comes from a Hypothesis strategy and the expected value is that date.
2. **`parse_lenient` never raises another exception.** Arbitrary text, including lone surrogates,
   either returns a date or raises `NepDateError`. Any other exception fails the property.
3. **Strict and lenient agree.** For arbitrary text that `parse` accepts, `parse_lenient` returns
   the same date. If `parse` raises `NepDateError`, the property says nothing about lenient.
4. **Digits match `Lang`.** For `yyyy-MM-dd` and `yyyy/MM/dd`, the English output equals a local
   `str.format` template, and the Nepali output equals the same template translated by a local
   `str.maketrans` table. The table is written in the test, not imported from `nepdate`.
5. **Ordinals match `datetime.date`.** For a random Gregorian date in range, `to_ordinal` equals
   `datetime.date.toordinal`, `to_date` equals that date, and `from_ordinal` of that ordinal
   returns the same BS date.
6. **`add_months` matches a month-index oracle.** The oracle maps the BS year and month to a
   zero-based month index, adds `n`, reads the target length from `_calendar.MONTH_LENGTHS`, and
   computes CLAMP or SPILL without calling `add_months`. It uses the constructor only to build the
   expected result. Out-of-range expectations raise `NepDateError`.
7. **`str`, `isoformat`, `short` YMD and `long` without a weekday** round-trip through the parser
   that accepts their output. `long(weekday=True)` has no inverse because no parser drops a
   weekday name; that limit is written in the test docstring and the inventory.

AC:
- The inventory above lists every public parse and format entry point and names its guard or the
  missing property.
- The seven properties above exist, each with a named oracle in the test body.
- `uv run pytest tests/test_properties_format_parse.py` passes with 100 examples per property.
- A deliberately wrong oracle value breaks the property, checked once by hand and not committed.

## P9-02 Coverage-guided fuzzing with atheris

Add `atheris==3.1.0` to a new `fuzz` dependency group with the marker
`sys_platform == 'linux'`. Atheris 3.1.0 supports Python 3.11 to 3.14 on Linux. The group stays
out of the runtime and dev dependencies, and `uv.lock` records it.

Add three targets under `fuzz/`:

- `fuzz_parse.py` decodes arbitrary bytes to text and calls `NepaliDate.parse`.
- `fuzz_parse_lenient.py` does the same for `NepaliDate.parse_lenient`.
- `fuzz_format.py` decodes arbitrary bytes to a pattern and calls `format` and `__format__` on a
  fixed valid date.

Decoding uses `surrogateescape`, so every byte string becomes a `str` and lone surrogates reach
the scanner. `NepDateError` is the only exception the parse targets catch. Any other exception,
including a crash, is a finding. The format target catches nothing. The harnesses do not commit a
corpus; `fuzz-artifacts/` is ignored and the artifact prefix is outside the repository.

Local budget: 60 s per target, at most 3 targets in parallel. Save the tool output and the
execution count under `docs/fuzz/<date>/`. If a target finds an input, stop P9 immediately, add the
minimal regression test under `tests/` with `@pytest.mark.xfail(strict=True, reason=...)`, and report
the input, traceback and target.

`.github/workflows/fuzz.yml` runs all three targets weekly and by dispatch, with a 300 s budget
each. `release.yml` gets the same matrix job, and both publish jobs need it. Actions are pinned by
full SHA and the jobs use `contents: read`. No pull-request trigger is added.

AC:
- `uv lock --check` passes; `atheris==3.1.0` is in `fuzz` with the Linux marker only.
- All three targets run for 60 s each locally; the logs and per-target execution counts are
  committed.
- No crash and no non-`NepDateError` exception is found. If one is found, P9 stops at the
  regression test and later ACs are not claimed.
- `fuzz.yml` has `schedule` and `workflow_dispatch` only, uses 300 s per target, and no workflow
  runs fuzzing on `pull_request`.
- No corpus is committed, and `fuzz-artifacts/` is ignored.

## P9-03 API compatibility gate

Add `scripts/api_snapshot.py`. It imports `nepdate` and `nepdate_patro`, reads each `__all__`, and
writes a sorted JSON snapshot to `docs/api-snapshot.json`. The snapshot records:

- each public name and its kind (constant, class, function, enum);
- constructor and method signatures from `inspect.signature`;
- property annotations;
- enum member names and values;
- class base names, so `NepDateError(ValueError)` is checked;
- the value of `MIN` and `MAX`.

`--write` regenerates the snapshot. `--check` compares the current surface with the snapshot:
a removed or changed entry fails; an added entry fails unless `docs/API.md` contains its
declaration. A declaration is a `def` line with the same signature (ignoring `self` and `cls`), a
`name: type` line for a property or constant, an enum member line with its value, or a `class`
line. A name that appears only in prose does not count.

`scripts/tests/test_api_snapshot.py` covers the checker with negative controls: a renamed item, a
changed signature, an undocumented addition, and a name present only in prose. A documented
addition passes. A changed exception base fails.

ADR-0010 records the snapshot format, the gate and the docs rule. ADR-0004 and the other accepted
ADRs are not edited. Add gate 10 to `scripts/ci.py`; its last line becomes
`ci: 10/10 gates passed`.

AC:
- `docs/api-snapshot.json` is generated by the script, sorted and stable across two runs.
- The checker fails on each of the four negative controls and passes the documented addition.
- `scripts/ci.py` runs the checker as gate 10 and prints `ci: 10/10 gates passed`.
- ADR-0010 is Accepted and indexed in `docs/adr/README.md`; no older ADR is edited.

## P9-04 Remove the dead weekday argument

Run the API gate with the P9-03 snapshot before the change. Remove the `weekday` parameter from
`format_pattern`, pass `0` to `format_long` for the `D` pattern, and remove the argument from the
call in `NepaliDate.format`. `long(weekday=True)` keeps its own `format_long` argument and output.
Run the API gate again: the snapshot must be unchanged.

Rerun mutmut on WSL with `--max-children 4` and save the new raw output, `stats.json`,
`summary.json` and `diffs.txt` under `docs/mutation/2026-10-18/`. Update
`docs/mutation/equivalent.md` so every survivor has one proof. The `weekday` equivalence rows
must disappear. The P8 table has five: three on `NepaliDate.format` and two on `format_pattern`.
The task text says four; the committed table is the count that matters.

The floor stays 95.00 % unless the measured score rises, then it is rounded down to a whole
percentage. If the floor changes, add ADR-0011 to supersede ADR-0009 rule 5, update
`scripts/mutation_check.py` and `docs/mutation.md`, and do not edit ADR-0009. If the score falls
below 95.00 %, add killing tests before the checkpoint.

AC:
- The API snapshot is byte-identical before and after the change.
- `long(weekday=True)`, `format("D")` and every golden format row still pass.
- The new mutation run uses 4 children; raw results and `summary.json` are committed.
- `equivalent.md` has one section, every survivor has a proof, and no row mentions `weekday`.
- The floor is 95.00 % or a higher whole percentage, recorded in the checker and the mutation
  docs. Every survivor is killed by a test or has an equivalence proof.

## Checkpoint

The reviewer checks:
- [ ] `uv run python scripts/ci.py` passes 10/10 and `release-check 0.1.0` passes.
- [ ] The property inventory and the seven new properties match the ACs, with independent
      oracles.
- [ ] The three atheris targets ran 60 s locally; execution counts and findings are reported.
- [ ] The API snapshot is committed, gate 10 fails on all four negative controls, and ADR-0010 is
      indexed.
- [ ] The private `weekday` argument is gone, the snapshot did not change, and the mutation score
      and floor are reported with the four rows removed.
- [ ] P7-02 to P7-05, ADR-0008, `benchmarks/` and `docs/benchmarks.md` are untouched.
- [ ] No tag, publish, remote, settings or secrets change; no corpus is committed.

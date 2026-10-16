# Progress (Python port)

Tasks from [`00-ROADMAP.md`](00-ROADMAP.md), in the format of the hub's `docs/handover.md` §3 step 7.
There is no GitHub remote yet: "CI last line" is `uv run python scripts/ci.py` run locally, and
GitHub-side tasks are blocked on the human.

| Task | Status | Commit | CI last line | Notes and open questions |
|---|---|---|---|---|
| P0-01 | done | 66ed8a5 | `ci: 7/7 gates passed` | uv workspace with the core at the root and `nepdate-patro` as a member. Two wheels and two sdists build; the core wheel has no `Requires-Dist` naming `nepdate-patro`. The lock file is committed. |
| P0-02 | done | 29ab343 | `ci: 7/7 gates passed` | `scripts/codegen.py` validates the 299 years of month lengths (29 to 32), writes `_calendar.py` and the patro `LICENSE`/`NOTICE` copies. `--check` exits 1 on drift; a length of 33 exits non-zero. |
| P0-03 | done | d28e976 | `ci: 7/7 gates passed` | `scripts/ci.py` runs the seven ADR-0004 gates in order and stops at the first failure. Gates 6 and 7 test the built wheels in throwaway venvs. Ruff skips the read-only `shared/` copy. |
| P0-04 | done | 023caa8 | `ci: 7/7 gates passed` | `conftest.py` resolves the repository root from `__file__`, so `uv run pytest` started inside `tests/` still finds `shared/spec/vectors/`. Scripts are loaded with importlib; `_archive_contains` and codegen validation get unit tests. |
| P0-05 | done | 8f8edb1 | `ci: 7/7 gates passed` | `ci.yml` (matrix per ADR-0004 plus 3.14t and the allowed-to-fail 3.15 pre-release, hub `shared-check`), `shared-sync.yml` (weekly), Dependabot, PR and issue templates, `SECURITY.md`, `CONTRIBUTING.md`. Every action pinned by full SHA. Not run on GitHub yet. |
| P0-06 | blocked | | | Human tasks: create `sanamhub/nepdate-python` with branch protection; settle the core distribution name; register the four pending trusted publishers; create the `production` and `testpypi` environments. See "Name" below. |
| P0 checkpoint | ready for review | 8f8edb1 | `ci: 7/7 gates passed` | All five code tasks done; P0-06 is the owner's. Blocked (human): GitHub repository and remote, branch protection, trusted publishers, environments. |
| P1-01 | done | 50f40b9 | see P1 checkpoint | `scripts/codegen.py` writes the ADR-0002 §3 tables into `_calendar.py`: `MONTH_LENGTHS` (3588), `MONTH_START` and `MONTH_START_ORD` (3589 each), `YEAR_START` (300), `MONTH_YEAR` and `MONTH_NUM` (3588 each), `BUCKET` (3413), `ORDINAL_OFFSET` (673243). The generator asserts the two-step bucket bound; a negative-control test feeds a table needing more steps and expects a non-zero exit. |
| P1-02 | done | 65ee46b | see P1 checkpoint | `_names.py` (`Lang`, `Month`, `Weekday`) and `_errors.py` (`ErrorKind`, `NepDateError` with a read-only `kind`). |
| P1-03 | done | 0be3d03 | see P1 checkpoint | `NepaliDate` with the four slots, `type(x) is int` fast path, bool and float rejection, `operator.index`, ALGORITHM §3 error precedence, read-only properties, comparisons and hash on `_o`, and `_from_parts`. |
| P1-04 | done | 6c9a2b0 | see P1 checkpoint | Bucket-lookup conversion (`to_date`, `to_ordinal`, `from_date`, `from_ordinal`), `weekday`, `day_of_year`, `month_length`, `month_enum`, `first_of_month`, `last_of_month`, `MIN`, `MAX`. No bisect, divmod or loop on the hot path. |
| P1-05 | done | db98021 | see P1 checkpoint | `test_vectors.py` (7176 month boundaries, 1018 golden dates), `test_exhaustive.py` (109,212 round trips plus a bisect reference), `test_properties.py` (hypothesis), `test_csharp_catalog.py` (one function per phase-1 row). 104 passed, 52 skipped in `tests/`. |
| P1 checkpoint | ready for review | db98021 | `ci: gate 5 (import-time) failed: import nepdate takes 8413 us, limit 5000` | Gates 1-4, 6 and 7 pass. Gate 5 fails on this machine: `import enum` alone takes 2.7 to 5 ms because Windows Defender (MsMpEng), VBCSCompiler, two Java daemons and SQL Server run in the background, so the ADR-0002 §7 budget of 5 ms, measured on the quiet reference machine, is not met here. `import nepdate` measured 6.7 to 26 ms across fresh `-X importtime` runs in this session. |
| P2-01 | done | 5f204e0 | `ci: 7/7 gates passed` | `add_days`, `days_until`, `__add__`/`__sub__` with timedelta, and the golden `add-days.tsv` (9162 rows). A fractional timedelta raises `NepDateError` (D-03). |
| P2-02 | done | d41f97f | `ci: 7/7 gates passed` | `add_months`/`add_years` with `Overflow.CLAMP`/`SPILL` via `divmod`, and the golden `add-months.tsv` (10180 rows). |
| P2-03 | done | 1b971e6 | `ci: 7/7 gates passed` | `diff` (ALGORITHM §8a) and the frozen `DateDiff` dataclass, with the P2-03 table and hypothesis properties. |
| P2-04 | done | f0cdcf9 | `ci: 7/7 gates passed` | `FiscalYear` and `Quarter` (ALGORITHM §8b), the golden `dates.tsv` `fy_start`/`fy_end`/`quarter_start`/`quarter_end` columns, and `FiscalYear(2082).label(Lang.NE) == "२०८२/८३"`. |
| P2-05 | done | 042ea68 | `ci: 7/7 gates passed` | `DateRange` with `len` computed from ordinals, iteration built from serials via `_from_serial`, and no set operations (D-09). Committed before P2-04 because `FiscalYear.range` returns a `DateRange`. |
| P2-06 | done | 94ce60d | `ci: 7/7 gates passed` | One function per C# catalogue row tagged phase 2 (180 rows): 103 real, 4 D-02, 65 n/a, 8 pending P4-03 (`today()`). Plus the `add_days` inverse property (d0f6268). |
| P2 checkpoint | ready for review | d0f6268 | `ci: 7/7 gates passed` | All seven gates pass. New stdlib import: `dataclasses` (frozen `DateDiff`), added to `CORE_IMPORT_ALLOWED` with its transitive imports in c4ace21. B3 ~894 ns and B4 ~840 ns (targets 400/350), measured with `timeit` on the loaded machine; not targets until P5. |

## Name (P0-06)

Checked against the PyPI JSON API on 2026-10-17:

| Name | Status | Evidence |
|---|---|---|
| `nepdate` | taken | Samir Maharjan, "Gets today's nepali date", versions 0.0.2 to 0.0.4, all uploaded 2021-09-22, no repository link |
| `nepdate-bs` | free | 404 from `pypi.org/pypi/nepdate-bs/json` |
| `nepdate-patro` | free | 404 from `pypi.org/pypi/nepdate-patro/json` |
| `pynepdate` | free | 404 from `pypi.org/pypi/pynepdate/json` |
| `nep-date` | free | 404 from `pypi.org/pypi/nep-date/json` |

The core distribution name stays `nepdate` until the owner decides. If the owner picks
`nepdate-bs`, the switch is one place per file: the core `[project] name`, the patro `dependencies`
entry and the patro `[tool.uv.sources]` key. The import name stays `nepdate` either way.
| P0 review | merged | see git log | `ci: 7/7 gates passed` | Reviewer fixed: `ci.py` now reads both distribution names from the pyproject files (the "three spots" claim missed the hardcoded wheel prefix, coverage target and patro range; a trial rename to `nepdate-bs` passes 7/7), CI runs `uv run --locked` (an unlocked dependency change fails). Open for the owner: PyPI name (`nepdate` is taken by a 2021 package), remote, trusted publishers, environments. CODE_OF_CONDUCT comes with the publish-ready phase. |
| P1 review | done | this commit | `ci: 7/7 gates passed` | Reviewer: gate 5 measured stdlib load, not ours (`import enum` alone 2.7 to 5 ms on the loaded machine; the package's own self time still swung 4 to 7 ms), so no absolute budget is stable in CI. Gate 5 now checks what each import loads: `import nepdate` may add only its own modules plus `__future__`, `_datetime`, `datetime`, `enum`; `import nepdate_patro` adds only its own. It keeps a 50 ms ceiling for gross regressions. Negative control: `import json` in the core fails with the 12 extra modules named. The ADR-0002 §7 5 ms budget, and B1/B2, move to the P5 quiet-machine benchmark. Exhaustive 109,212 round-trip plus bisect reference, and the five negative controls, accepted |

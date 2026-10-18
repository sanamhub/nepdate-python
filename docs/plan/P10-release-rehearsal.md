# P10: CI matrix parity, freshness gates and release rehearsal

Read first: ADR-0004, ADR-0005, ADR-0006, ADR-0010, [`docs/API.md`](../API.md), the P9 review
row in [`PROGRESS.md`](PROGRESS.md), the hub H1-02 rule and the Rust W4-00 plan. P7-02 to P7-05 stay
parked: this phase does not run benchmarks or change ADR-0008, `benchmarks/` or
`docs/benchmarks.md`.

The P9 review ran the gates on Python 3.11, 3.12 and 3.13 and found two gate 5 failures that the
local 3.13-only runs had hidden. There is no GitHub remote yet, so the matrix in `ci.yml` is a
promise the local work did not keep. P10 adds a local runner that reads that matrix, a release gate
for stale patro data, a rehearsal of the four release artifacts, and a check that the public names
and ADRs stay visible in the docs.

## Rules for this phase

- No public API or behaviour change. The API snapshot is the baseline; a difference stops the
  phase.
- Toolchains and caches go under `D:\devcache\p10` on Windows and `/mnt/d/devcache/p10` in WSL,
  never on C:. At most 4 jobs run at once; the matrix runner starts at most 2 Python versions.
- No tag, publish, remote, settings or secrets change. No upload of a rehearsal artifact.
- No AI attribution in commits or docs.

## P10-00 Plan

This file, the roadmap row and the progress row, committed before any implementation. AC:
- The plan names every task from P10-00 to P10-04, the tools and versions, the limits and the
  checkpoint report.
- The roadmap and progress tables link this file and the P10 task IDs.
- No production code or dependency changes in this task.

## P10-01 Local CI matrix

Add `scripts/ci_matrix.py`. It reads the `test` matrix from `.github/workflows/ci.yml`, keeps the
unique `python` values in file order, and runs `uv run --locked python scripts/ci.py` once per
version. The 3.15 pre-release is a separate job and is not part of the matrix. The 3.14t entry is
kept as `3.14t`.

- Each run gets its own `UV_PROJECT_ENVIRONMENT` under `D:\devcache\p10\envs\<slug>`, plus
  `UV_PYTHON_INSTALL_DIR=D:\devcache\p10\python` and `UV_CACHE_DIR=D:\devcache\p10\uv-cache`.
  They can be overridden with `--cache-root`, `--python-dir` and `--jobs`; the default job count
  is 2 and the maximum is 4.
- A version that `uv python find` cannot provide is printed as `skip` and counted as skipped, not
  as passed. A skip does not fail the command when at least one version ran; the summary line says
  how many ran, passed, failed and skipped.
- `--list` prints the matrix versions without running anything. `--dry-run` prints the command and
  environment for each version. The exit code is 0 when every run that started passed, 1 when any
  run failed, and 2 for a missing or unreadable workflow.
- The script does not copy the version list. A test writes a temporary `ci.yml` with `3.99` and
  another with `3.11` removed, and asserts that the parsed list changes. That is the negative
  control: a hardcoded list would return the same versions for both files.

AC:
- `uv run python scripts/ci_matrix.py --list` prints `3.11`, `3.12`, `3.13`, `3.14`, `3.14t` from
  the committed workflow.
- `uv run python scripts/ci_matrix.py` runs `scripts/ci.py` on every version uv can provide, with
  at most 2 processes, and prints one `ci: 10/10 gates passed` line per version that ran.
- `uv run pytest scripts/tests/test_ci_matrix.py` passes, including the temporary-workflow
  negative control and a missing-version skip.

## P10-02 Data freshness gate

Add `scripts/data_status.py`. It reads `shared/data/patro/*.json` directly, not the generated
`_tables.py`, and reports the first and last BS date for tithi, public holidays and events.

- The last BS date is converted with the installed `nepdate`, and `days_left` is
  `(last_ad - today).days`. `today` is the local date unless `--today YYYY-MM-DD` is given.
- Public holidays are the release blocker: fewer than 183 days left exits 1 and names the holiday
  range. Tithi and events print a `WARNING` line and do not fail. Exactly 183 days passes.
- Missing public holiday data fails. Missing tithi or event data warns.
- `scripts/ci.py release-check VERSION` includes the holiday failure. `scripts/ci.py data-status`
  is the standalone command; both accept `--today`.

AC:
- `uv run python scripts/data_status.py --today 2027-06-03` exits 0 on the committed data, because
  public holidays end 183 days later; `--today 2027-06-04` exits 1 because 182 days are left.
- `uv run python scripts/data_status.py` prints a tithi warning and exits 0 on 2026-10-18.
- A synthetic range with 183 days left passes and one with 182 fails, in
  `scripts/tests/test_data_status.py`. The same test checks the warning-only path and missing data.
- `scripts/ci.py release-check 0.1.0` fails on a temporary tree whose holiday data ends 182 days
  after the supplied `--today`.

## P10-03 Release rehearsal

Add a `release` dependency group with a pinned `twine`. Add `scripts/rehearsal.py`; `release-check`
runs it after the version, data and changelog checks. It builds both sdists and both wheels into a
temporary directory, with `uv build --all-packages --out-dir`, and checks:

1. `twine check` passes all four files.
2. Neither wheel contains a path component named `tests`, `fuzz` or `docs`, nor a `test_*.py`
   file. The core wheel has only `nepdate/` and the dist-info; the patro wheel only
   `nepdate_patro/` and the dist-info.
3. The core sdist contains `LICENSE`, `shared/data/NOTICE` and the shared calendar source
   `shared/data/calendar/bs-calendar.json`. The patro sdist contains `LICENSE`, `NOTICE`,
   `shared/data/patro/*.json` and the generated `_tables.py`. The root `pyproject.toml` gains
   `source-include = ["shared/data/calendar/**"]`; the release build stages the patro JSON beside
   the patro package and adds the same include there. The wheels are unchanged.
4. Both `pyproject.toml` versions, the `CHANGELOG.md` top dated section, both wheel `METADATA`
   versions and the version `importlib.metadata.version` reports after installing each wheel all
   agree. The source `__init__.py` has no version literal; ADR-0005 keeps the version in
   `pyproject.toml`, so the installed package metadata is the `__init__` side of the check.

The rehearsal writes nothing to `dist/`, uploads nothing and does not need a network connection
after the release group is installed. A negative control removes one required file from a copy of
an archive and expects a failure, and a synthetic wheel with `tests/test_x.py` fails the wheel
check.

AC:
- `uv run python scripts/ci.py release-rehearsal` prints `release: 4 artifacts checked` and exits
  0 on the branch.
- `uv run python scripts/ci.py release-check 0.1.0` runs the same rehearsal and still prints
  `release: 0.1.0 is consistent`.
- `scripts/tests/test_rehearsal.py` covers the missing shared calendar file, the `tests/` wheel
  member, a version mismatch and a `twine check` failure on a malformed copy.
- [`docs/release.md`](../release.md) documents the commands, the four artifacts, the twine pin and
  the freshness rule.

## P10-04 Docs drift

Add `scripts/tests/test_docs_drift.py` and a README API table.

- Every name in `nepdate.__all__` and `nepdate_patro.__all__` is declared in `docs/API.md` (the API
  gate already checks this) and appears in the README API table, or as the label of a Markdown
  link to a docs page. The README table lists the core names and the patro names in one place and
  links the API page.
- Every `docs/adr/NNNN-*.md` file has one row in `docs/adr/README.md`, and every row points at an
  existing ADR file. The check compares the two sets.
- Negative controls: a temporary README with `NepaliDate` removed fails, and a temporary ADR
  directory with an extra file but no row fails. Adding the name as a link label passes.

AC:
- `uv run pytest scripts/tests/test_docs_drift.py` passes.
- The test fails when one exported name is deleted from a copy of the README and when one ADR row
  is deleted from a copy of the ADR README.

## Checkpoint (stop here for review)

The reviewer checks:
- [ ] `scripts/ci_matrix.py --list` matches `ci.yml`; every local Python that ran printed
      `ci: 10/10 gates passed`, and any skipped version is named as skipped.
- [ ] `scripts/data_status.py` exits 1 at 182 days and 0 at 183, with the holiday range named.
- [ ] `scripts/ci.py release-check 0.1.0` builds and checks all four artifacts with `twine check`,
      and the rehearsal output names each one.
- [ ] The README API table and `docs/adr/README.md` match the exported names and the ADR files.
- [ ] No tag, publish, remote, settings, secrets, benchmark or ADR-0008 change.

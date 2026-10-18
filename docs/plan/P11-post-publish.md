# P11: Release notes and post-publish verification

Read first: ADR-0005, ADR-0011, the P10 review row in [`PROGRESS.md`](PROGRESS.md),
[`docs/release.md`](../release.md), [`CHANGELOG.md`](../../CHANGELOG.md) and
[`.github/workflows/release.yml`](../../.github/workflows/release.yml). P7-02 to P7-05 stay parked:
this phase does not run benchmarks or change ADR-0008, `benchmarks/` or `docs/benchmarks.md`.

The 0.1.0 release was never published. The `[Unreleased]` section still holds the `nepdate-core`
rename, so the GitHub Release notes for 0.1.0 would omit a change that is part of that version.
ADR-0005 describes a job that installs both published versions, runs the README example and makes
one `nepdate_patro.info` call. The workflow has no such job. P11 moves the entry into 0.1.0, makes
an entry under `[Unreleased]` a release failure, and adds verification for both PyPI and TestPyPI.

## Acceptance criteria

- `CHANGELOG.md` has an empty `[Unreleased]` section, and the `nepdate-core` rename is listed under
  `[0.1.0]`.
- `scripts/ci.py release-check 0.1.0` fails when the `[Unreleased]` section has content, and passes
  when it is empty. Two tests cover the empty and non-empty cases.
- `release.yml` has a `verify` job that needs `publish`, and a `verify-testpypi` job that needs
  `publish-testpypi`.
- Each verify job installs `nepdate-core==X.Y.Z` and `nepdate-patro==X.Y.Z` into a clean virtualenv,
  retries for up to 10 minutes, runs the README quick start and one `nepdate_patro.info` call.
- Each verify job pins every external action by SHA, sets `permissions: contents: read` and has no
  `id-token` permission.
- `scripts/tests/test_release_workflow.py` passes and its negative controls fail a workflow with a
  missing job, wrong `needs` and an `id-token` permission.
- `docs/release.md` describes both verify jobs and says to yank both distributions and publish the
  next patch when verification fails.
- `uv run python scripts/ci_matrix.py --cache-root D:\devcache\p11` passes on every version uv can
  provide and reports the summary line.
- No public API or behaviour change. No tag, publish, remote, settings or secrets change. No
  benchmark run and no change to ADR-0008, `benchmarks/` or `docs/benchmarks.md`.

## Rules for this phase

- No public API or behaviour change. The API snapshot is the baseline; a difference stops the
  phase.
- Toolchains and caches go under `D:\devcache\p11` on Windows and `/mnt/d/devcache/p11` in WSL,
  never on C:. At most 4 jobs run at once; the matrix runner starts at most 2 Python versions.
- No tag, publish, remote, settings or secrets change. No TestPyPI or PyPI upload.
- No AI attribution in commits or docs.

## P11-00 Plan

This file, the roadmap row and the progress rows, committed before any implementation.

AC:
- The plan names every task from P11-00 to P11-03, the tools and versions, the limits and the
  checkpoint report.
- The roadmap and progress tables link this file and the P11 task IDs.
- No production code, workflow or dependency change in this task.

## P11-01 Release notes

Move the `nepdate-core` rename from `[Unreleased]` into `[0.1.0]` under `### Changed`, after the
`### Added` list. Leave `[Unreleased]` with no entries; 0.1.0 was never published, so the rename
belongs to 0.1.0.

`scripts/ci.py` reads the body of `## [Unreleased]` up to the next version heading. Any non-blank
content fails `release-check` with a message naming `[Unreleased]`. An empty section passes. A
missing `[Unreleased]` heading is not an error in this task.

AC:
- `uv run python scripts/ci.py release-check 0.1.0` prints `release: 0.1.0 is consistent` on the
  branch, with the existing tithi warning.
- `test_release_check_passes_with_empty_unreleased` passes on a temporary changelog with an empty
  `[Unreleased]` section.
- `test_release_check_rejects_unreleased_entries` fails on a temporary changelog with a bullet
  under `[Unreleased]`, and the message names `[Unreleased]`.
- The committed changelog has no content between `## [Unreleased]` and `## [0.1.0]`, and the
  rename is in the 0.1.0 section.

## P11-02 Verify job

Add two jobs to `.github/workflows/release.yml`:

| Job | Needs | Index |
|---|---|---|
| `verify` | `preflight`, `publish` | `https://pypi.org/simple/` |
| `verify-testpypi` | `preflight`, `publish-testpypi` | `https://test.pypi.org/simple/` |

Both jobs run on `ubuntu-latest` with `permissions: contents: read`, no `id-token`, and every
external action pinned by full SHA. Each creates a venv under `$RUNNER_TEMP/verify`, then runs
`uv pip install --no-cache --index-url "$INDEX_URL"` for the exact two versions. The version comes
from `needs.preflight.outputs.version` through an `env` entry, never from an expression inside a
`run` line.

The install retries on failure for up to 600 seconds with a 30 second pause between attempts. The
job then runs the README quick start (construction, `str`, `to_date`, Nepali `long`, `parse`) and
one `nepdate_patro.info` call that checks the tithi label. The install and the code use the clean
venv's interpreter, not the checkout or the runner's Python environment.

AC:
- `uv run pytest scripts/tests/test_release_workflow.py` passes with both jobs present.
- The test reads the workflow and rejects a missing `verify` or `verify-testpypi` job, a job whose
  `needs` omits its publisher, and a job with `id-token: write`.
- The shipped workflow contains the 600 second retry window, both exact pins, the PyPI and TestPyPI
  index URLs, the README quick start and one `nepdate_patro.info` call.

## P11-03 Release runbook

Add an "After the publish" section to [`docs/release.md`](../release.md). It names `verify` for a
tag run and `verify-testpypi` for a dispatch dry run, and says what each job installs and runs.

If verification fails, the release is not done. Do not upload the same files again and do not
publish a different build under the same version. Yank both distributions for that version, fix
the cause, and publish the next patch version of both, as ADR-0005 says. A TestPyPI failure is a
failed rehearsal; yank both TestPyPI files and use the next patch version.

AC:
- `docs/release.md` has the two job names, the 10 minute retry, the exact install and the quick
  start.
- The failure paragraph says yank both and publish the next patch, for PyPI and TestPyPI.
- `uv run python scripts/docs_check.py` passes.
- The README documentation table describes the release page as including post-publish
  verification.

## Checkpoint (stop here for review)

The reviewer checks:
- [ ] `CHANGELOG.md` has an empty `[Unreleased]` and the rename under `[0.1.0]`.
- [ ] `release-check` rejects a non-empty `[Unreleased]` and accepts an empty one, with both tests.
- [ ] `verify` and `verify-testpypi` follow their publish jobs, use SHA-pinned actions, read-only
      permissions, exact pins and the 10 minute retry.
- [ ] `docs/release.md` covers the verify jobs and the yank and next-patch response.
- [ ] `scripts/ci_matrix.py --cache-root D:\devcache\p11` passes and its summary line is reported.
- [ ] No tag, publish, remote, settings, secrets, benchmark or ADR-0008 change.

# P8: Mutation testing

Read first: ADR-0004, ADR-0006, ADR-0008, [`P7-quiet-bench.md`](P7-quiet-bench.md), and the Go
port's `docs/plan/G8-mutation-testing.md` and `G9-mutation-scope.md`.

P7-02 to P7-05 stay parked; this phase does not run benchmarks or change ADR-0008,
`benchmarks/` or `docs/benchmarks.md`. Mutation testing measures the tests, not the library: a
surviving mutant is a test gap, and the answer is a new test or a written equivalence argument.
Production code is never weakened to raise the score.

## Tool

**mutmut 3.8.0**, pinned in a new `mutation` dependency group. Mutmut selects the tests that cover
the mutated function, so a mutant in a small helper does not rerun the 712-test suite. That is the
reason it beats cosmic-ray here: a dry `cosmic-ray init` on the core with `_calendar.py` excluded
produced 3295 mutants, and cosmic-ray runs the full `test-command` for each one.

Mutmut 3 needs `fork`, so the local Windows run uses WSL Ubuntu 26.04. GitHub Actions uses
`ubuntu-latest`. The WSL clone, virtualenv and pip cache stay off the C: drive where the wrapper
can place them; tool downloads and caches go under `D:\devcache\p8`.

## Tasks

### P8-00 Plan
This file, the roadmap row and the progress row. Commit before the first tool install or mutation
run.
AC:
- The plan names the tool, version, scope, worker limit, result format, floor rule and every later
  task.
- The P7 parked tasks and the no-benchmark rule are stated.

### P8-01 Tool and scope
Add `[dependency-groups] mutation = ["mutmut==3.8.0", "pytest-cov==7.1.0", "hypothesis==6.170.1"]`,
pin the same versions in `uv.lock`, and add one `[tool.mutmut]` section with:
- `source_paths`: `src/nepdate` and `packages/nepdate-patro/src/nepdate_patro`;
- `do_not_mutate`: `*_calendar.py` and `*_tables.py`;
- `pytest_add_cli_args_test_selection`: `tests` and `packages/nepdate-patro/tests`;
- `also_copy`: `shared` and `packages/nepdate-patro/tests`;
- `pytest_add_cli_args`: `-x -q --no-header -p no:cacheprovider --ignore=tests/test_source_hygiene.py`.
  That test parses the installed source and cannot run against mutmut's generated trampolines.
- 4 children on the command line: `mutmut run --max-children 4`.
ADR-0009 records the tool, the scope, the floor rule and the jobs. Status stays Proposed until the
floor is known.
AC:
- `uv lock --check` passes after the group is added; the group is not in the runtime or dev
  dependencies.
- `mutmut run --max-children 4` starts from the WSL copy with the configured scope and excludes the
  two generated files.
- ADR-0009 exists and has no em dash.

### P8-02 First full run
Run both packages with at most 4 children in one WSL session. Save the raw tool output
(`mutmut results --all`, `mutmut export-cicd-stats`) and `summary.json` under
`docs/mutation/<date>/`; the summary records wall time, worker count, tool version and the counts
for killed, survived, timeout and suspicious, per module.
AC:
- The raw output and `summary.json` are committed.
- The summary quotes the tool's own summary line.
- No run used more than 4 children.

### P8-03 Triage
Every survivor gets one disposition:
- a new or tightened test that kills it, placed next to the tests for that module, one behaviour
  per test, named after the behaviour; or
- a row in `docs/mutation/equivalent.md` with the mutant id, the diff and a one-line proof of
  equivalence. "Hard to test" is not equivalence.
Run both packages again after the tests. The floor is set from this score, rounded down, and is
recorded in ADR-0009 and the gate.
AC:
- Every survivor from P8-02 has a killed-by test name or an equivalent row.
- The final score and survivor count are recorded before and after triage.
- ADR-0009 is Accepted with the measured floor.
- No production code is weakened.

### P8-04 Automation
`scripts/mutation_check.py` reads a mutmut stats export, the equivalent list and the floor. It
exits non-zero when the score is below the floor or a killed mutant is not in the list. Tests in
`scripts/tests/test_mutation_check.py` cover pass, below-floor (negative control), an unlisted
equivalent, a duplicate id and a malformed export.
Add a `mutation` job to `release.yml` that runs both packages and then the checker, so a release
below the floor is blocked. Add `.github/workflows/mutation.yml` with a weekly `schedule` and a
manual dispatch, no pull-request trigger. The gate is outside `scripts/ci.py`; the last line stays
`ci: 9/9 gates passed` and no per-PR gate is added.
AC:
- The checker fails below the floor with a non-zero exit and names the score and floor.
- `release.yml` publish needs the mutation job.
- The weekly workflow has `schedule` and `workflow_dispatch` only.
- No mutation job runs on `pull_request`.

### P8-05 Docs
Add `docs/mutation.md`: how to run both packages locally, the 4-child limit, what the floor means,
how to add an equivalent and how the release and weekly jobs use the result. Link it from the
README documentation table.
AC:
- `scripts/docs_check.py` passes and `docs/mutation.md` has no em dash.
- The commands in the page match the committed configs and script.

## Checkpoint

The reviewer checks:
- [ ] `uv run python scripts/ci.py` passes 9/9 and `release-check 0.1.0` passes.
- [ ] The `mutation` group is pinned and outside the runtime and dev dependencies.
- [ ] The raw P8-02 run and `summary.json` are committed, with wall time and 4 children.
- [ ] The score before and after triage is quoted from the tool, and the floor is set from it.
- [ ] Every survivor is killed by a named test or has an equivalent row with a diff and a proof.
- [ ] `scripts/mutation_check.py` has the negative control and the weekly/release jobs are
      configured as above.
- [ ] `docs/mutation.md` is linked and passes the docs gate.
- [ ] P7-02 to P7-05, ADR-0008, `benchmarks/` and `docs/benchmarks.md` are untouched.
- [ ] No tag, publish, remote, settings or secrets change.

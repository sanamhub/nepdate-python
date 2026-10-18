# P6: Core name, import cost, release guard, competitor detail

Read first: ADR-0002 §7, ADR-0005, ADR-0006, `docs/competitors.md`, `docs/benchmarks.md`.

This plan was written at review time from the task list the agent was given; every task is done.
The P6 review is in `PROGRESS.md`.

## Tasks

### P6-01 Rename the core distribution (done, 8e93826)
The core distribution is `nepdate-core`; the import name stays `nepdate` (ADR-0007). Change the
core `[project] name`, the patro dependency and the patro `[tool.uv.sources]` key, and every
install line in the READMEs, runbook and docs.
AC: gates 6, 7 and 9 build, inspect and install `nepdate_core-0.1.0`; `release-check` fails when
the patro dependency names the import name `nepdate` (a test on a temporary copy).

### P6-02 Import cost (done, 2eaf4e9; partly reverted in review)
Measure `import nepdate` before and after, in alternating fresh processes, with the load sampled.
Defer tables that `import nepdate` does not need, without putting an import on a benchmarked path.
Record the result and any budget proposal in a new ADR; ADR-0002 §7 stays untouched.
AC: the lenient parser loads on the first `parse_lenient` call; `tests/test_lazy_imports.py` pins
which modules load with the package; B1 to B8 are not slower; ADR-0008 is Proposed and gate 5
keeps its 50 ms ceiling (ADR-0006).
Review note: deferring `_format` and `_pattern` made `str(d)` and B5 about 2.5 times slower, so
both are imported with the package again.

### P6-03 Release only from main (done, 79fafaf)
The PyPI publish job checks out full history, fetches `origin/main` and fails unless the tagged
commit is an ancestor of it, before any upload.
AC: `test_release_workflow.py` checks the checkout depth, the fetch, the `merge-base
--is-ancestor` call, `COMMIT_SHA: ${{ github.sha }}` and the order, with a negative example
that has no main check.

### P6-04 Every competitor miss (done, e5ac5f4)
`probe()` records each rejected or differing date per package and direction: input, their result,
ours, and whether the BS year is in 2087 to 2090. `docs/competitors.md` tabulates the rows.
AC: the counts in `probe.json` are unchanged; a test checks the counts, the row fields and the docs
table, with a negative control that removes one row.

## Checkpoint

- [x] `uv run python scripts/ci.py` passes 9/9 and `release-check 0.1.0` passes.
- [x] No leftover `nepdate` distribution name where `nepdate-core` is meant; the import name is
      unchanged.
- [x] B5 and `str(d)` are not slower than main (checked with `timeit` against a `main` worktree).
- [x] ADR-0008 is Proposed, amends ADR-0002 §7 without editing it, and has no em dash.
- [ ] Quiet-machine import and B1 to B8 run: open, see the P7 prompt.

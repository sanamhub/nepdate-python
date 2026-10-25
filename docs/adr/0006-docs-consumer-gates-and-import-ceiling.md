# ADR-0006: Docs and consumer gates, and the import-time ceiling

- Status: Accepted
- Date: 2026-10-18
- Deciders: Sanam Pakuwal
- Amends: ADR-0004 (gate list and gate 5)

## Context

ADR-0004 lists seven CI gates. Release preparation added two more, widened gate 3 to run the documentation
examples, and found that gate 5 as written in ADR-0004 (core import under 5 ms, patro under 10 ms)
is not what `scripts/ci.py` enforces. The script uses a 50 ms ceiling for each, because a loaded
CI runner cannot hold a 5 ms bound without flaking. ADR-0004 is Accepted and is not edited, so the
change is recorded here.

## Decision

1. **Gate 3** also runs the README doctests and the docstring examples in `_date.py`, `_range.py`
   and `nepdate_patro/__init__.py`, under the same coverage rule.
2. **Gate 5** keeps its two checks (no `nepdate_patro` entry in `import nepdate`, and the patro
   timing), the best of 3 runs, and the module allow-list, but its time limit is a coarse ceiling
   of 50 ms for the core and 50 ms for the patro. It catches a gross regression, not a budget
   miss.
3. The ADR-0002 §7 budgets (core under 5 ms, patro under 10 ms) stay the targets. They are
   measured by the benchmark suite (`benchmarks/import_time.py`) and reported in
   `docs/benchmarks.md` with the machine load. A budget miss is a tracked defect, not a CI failure.
4. **Gate 8, docs:** `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md` and `docs/*.md`
   have no em dash, no task ID and no relative link that does not resolve. Plans and ADRs keep
   their task IDs and are not part of this gate.
5. **Gate 9, consumer:** a fresh venv outside the repository gets the two built wheels and runs
   one BS to AD conversion and one `nepdate_patro.info` lookup. The venv has no pytest and no
   checkout on `sys.path`.

The last line of `scripts/ci.py` is `ci: 9/9 gates passed`, or names the gate that failed.

## Consequences

- An import-time regression of several milliseconds passes CI. Only the benchmark run shows it, so
  every release reads the import row of `docs/benchmarks.md`.
- On 2026-10-18 the core measured 7.3 ms in the gate run and 15.1 ms under heavier load, above the
  5 ms budget. This is open work, not an accepted state.

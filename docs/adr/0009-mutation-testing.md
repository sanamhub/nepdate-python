# ADR-0009: Mutation testing with mutmut

- Status: Accepted
- Date: 2026-10-18
- Deciders: Sanam Pakuwal
- Amends: ADR-0004 (a quality gate outside `scripts/ci.py`)

## Context

The Go port runs Gremlins on the hand-written core and patro files: 4 workers, a survivor baseline
per package, and a test-efficacy floor of 99.5 % (see the Go repository's ADRs). The Python suite has 712 tests, 98 % line coverage and a fast path that
must stay fast, so line coverage alone does not show whether the tests check behaviour.

For Python there are two practical tools. **mutmut 3.8.0** selects only the tests that cover a
mutated function, so a mutant in a helper does not rerun the full suite. It needs `fork`, so it
runs on WSL locally and on the Ubuntu CI runner. **cosmic-ray 8.7.0** runs the configured
`test-command` for every mutant. A dry `cosmic-ray init` over the core with `_calendar.py` excluded
produced 3295 mutants, so the full-suite-per-mutant cost is too high for this shared machine.

A mutmut smoke run over `nepdate._date` with 4 children produced 399 checked mutants in about 41 s
(9.63 mutations per second); 350 were killed and 49 survived. The full generated set was 1350
mutants with the two generated tables excluded, so a full run is minutes, not hours.

## Decision

1. The tool is **mutmut 3.8.0**, pinned in the `mutation` dependency group, not in the runtime or
   dev dependencies. `pytest-cov 7.1.0` and `hypothesis 6.170.1` are pinned there too, because the
   mutation run uses the real test suite.
2. The scope is `src/nepdate` and `packages/nepdate-patro/src/nepdate_patro`. The generated
   `_calendar.py` and `_tables.py` are excluded. The source-hygiene test is excluded from the
   mutation runs because it parses the installed source and the mutmut trampolines are not that
   source; every other test stays.
3. The run uses at most **4 children**. Results are saved under `docs/mutation/<date>/` with the
   tool output and a `summary.json` that records the wall time and the worker count.
4. Every survivor is killed by a named test or listed in `docs/mutation/equivalent.md` with the
   mutant id, the diff and a one-line proof. "Hard to test" is not equivalence.
5. The score floor is **95.00 %** of killed over killed plus survived, rounded down from the
   measured 95.12 %. Timed-out and no-test mutants are outside both counts, as in mutmut's own
   efficacy figure; the summary also records killed over all mutants (93.78 %). It is written in `scripts/mutation_check.py`. A release below it is blocked;
   the weekly run reports drift. There is no per-pull-request mutation gate, so `scripts/ci.py`
   stays at 9 gates.
6. The local Windows run uses WSL Ubuntu 26.04 because mutmut 3 needs `fork`. GitHub Actions uses
   `ubuntu-latest`. The package is not installed in the mutation environment: mutmut puts
   `mutants/src` first on `sys.path`, and the editable install would otherwise keep the tests on
   the unmutated source. The patro source is copied to `src/nepdate_patro` for the run so the
   mutant names match the imports.
7. The disposition table is `docs/mutation/equivalent.md`, with one section: equivalents, each
   with a proof. A survivor that a test could detect gets the test. `scripts/mutation_check.py`
   rejects any other section. Error wording is not API (callers match on `kind`), so a mutant
   that only rewords a message is equivalent; a blank message is not.
8. Module-level code runs once at import, before mutmut activates a mutant, so a mutant in a
   function called only at import (the patro table builder) is killed only by a test that calls
   the function itself against an independent oracle (the shared JSON).

## Results

The first full run on 2026-10-18 with 2 children: 1350 mutants, 1220 killed, 108 survived,
21 timed out, 1 had no tests, 4.85 mutations per second, 313 s. Test efficacy 91.87 %.

After the survivor fixes, with 4 children: 1350 mutants, 1266 killed, 65 survived, 18 timed out,
1 had no tests, 8.88 mutations per second. Test efficacy 95.12 %. A second run of the same tree
took 152 s (1263 killed, 21 timed out: three mutants move between killed and timeout with machine
load; the survivors are the same 65).

## Consequences

- A full run costs minutes, not a per-PR check. The release job and the weekly job are the
  enforcement points.
- The floor is a measured number, not a guess, and it is not set until the survivors are dispositioned.
- Mutant ids and diffs are tool output. A tool upgrade that changes ids is a deliberate baseline
  update, not a silent pass.
- Local runs need a WSL copy of the repository. The copy, virtualenv and pip cache are kept off the
  C: drive.

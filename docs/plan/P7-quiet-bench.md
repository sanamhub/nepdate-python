# P7: Quiet-machine measurements and the ADR-0008 decision

Read first: ADR-0002 §7, ADR-0008, `docs/benchmarks.md`, `benchmarks/README.md`,
`shared/spec/BENCHMARK.md`, the P6 plan and the P6 review row in `PROGRESS.md`.

P5 and P6 measured on a machine that was busy: the all-CPU load ranged from 20 to 100 %. This
phase takes no target verdict from a loaded run. If a quiet window does not come, every target
stays pending and the report says so.

## Protocol

- The batch runs only while the all-CPU load is under 15 %. The load is sampled before each run
  and while it runs, and the load of logical CPU 2 is recorded beside it, as the TypeScript port
  does in `bench/load.ts` and `bench/measure.ts`.
- Every measured process is pinned to logical CPU 2: `--affinity 2` for pyperf, and
  `start /affinity 4 /wait` for the C# benchmark.
- A row is eligible for a verdict only when its `load_before` (all CPUs, nothing pinned yet) and
  its `background_max` (every CPU except CPU 2, sampled while it runs) are both under 15 %. CPU 2
  is left out during the run because the benchmark keeps it busy by design. A row above either is
  marked `loaded: true` and is not a verdict.
- If no window comes, `benchmarks/results/<date>/quiet.json` records the attempts and every
  target stays pending. No loaded number is copied into a target column or used to accept or
  reject an ADR.

## Tasks

### P7-01 Quiet window
Add the pre-run load and the `loaded` flag to `benchmarks/run.py`, and record the session attempts
in `quiet.json`. The row keeps the existing during-run samples, so the report has a before value
and a max value.
AC: a run whose load is 15 % or more is marked loaded and cannot become a verdict; `quiet.json`
has one entry per attempt with the time, the all-CPU load, the CPU 2 load and whether it was
eligible.

### P7-02 Import
Run `benchmarks/import_time.py` for `import nepdate` and `import nepdate_patro`: five fresh
processes each, best of five. Measure the bare `datetime` plus `enum` floor in the same window.
Read the per-module self times from the best `-X importtime` output.
AC: `import_time.json` has the core, the patro and the floor with the load before each run; the
per-module self table is in `docs/benchmarks.md`; the P6 review state (`_format` and `_pattern`
eager, `_lenient` lazy) is the measured tree.

### P7-03 B1 to B8 and the C# column
Run `uv run --group bench python benchmarks/run.py --date <date>` with pyperf `--rigorous` inside
the same quiet window. Run the hub's `tools/dotnet-bench` on this machine in the same session:
`dotnet run -c Release -f net10.0 --project tools/dotnet-bench -- --filter "*" --artifacts <dir>`.
Record the load before the C# run and while it runs. Copy the BenchmarkDotNet Markdown and CSV
into `benchmarks/results/<date>/dotnet/`.
Before/after against `main` at `ebb4f9a` is required for B5 and `str(d)`, because P6 regressed
them and the review restored the eager imports. Use a `main` worktree or a source copy on
`PYTHONPATH`, and run the same `timeit` on both trees in the same window.
AC: the B1 to B8 table carries the load and the C# column; B5 and `str(d)` are no more than 10 %
slower than `main`; the before/after numbers are in `docs/benchmarks.md`.

### P7-04 ADR-0008 decision path
Choose exactly one outcome from the quiet import run:
- 5 ms core and 10 ms patro hold: mark ADR-0008 Rejected and write ADR-0009 saying the ADR-0002
  §7 targets hold.
- 15 ms core and 20 ms patro hold but 5 ms and 10 ms do not: leave ADR-0008 Proposed and give the
  owner the numbers to accept it. The agent does not accept it.
- 15 ms and 20 ms are missed: report a regression with a `cProfile` or importtime breakdown and
  change no target.
AC: the chosen path is recorded in `PROGRESS.md`, and ADR-0008's status matches it. If no quiet
window came, ADR-0008 stays Proposed and the path is "pending".

### P7-05 Misses
For each B1 to B8 miss in the quiet run, give a `cProfile` top 10 and one proposed change with
its expected gain. The proposal must not put an import or a cache on a hot path, and it must not
add module-level mutable state (AGENTS.md §2). No proposal is implemented in this phase.
AC: every declared miss has a profile and a proposal; a target that is pending has no miss row.

## Checkpoint

The reviewer checks:
- [ ] `uv run python scripts/ci.py` passes 9/9 and `release-check 0.1.0` passes.
- [ ] `quiet.json` shows a batch whose loads were under 15 %, or records that no window came and
      leaves every target pending.
- [ ] Every B1 to B8 row has `load_before`, `background_max` and `loaded`; no loaded row is a
      verdict.
- [ ] The import table has the core, the patro and the bare floor with the load.
- [ ] The C# column comes from this machine and this session, with its load.
- [ ] B5 and `str(d)` are compared with `main` and are not slower by more than 10 %.
- [ ] ADR-0008 is Rejected, left Proposed, or followed by ADR-0009, exactly as P7-04 says.
- [ ] Every declared miss has a `cProfile` top 10 and one proposal, and no proposal is implemented.
- [ ] No tag, publish, remote or settings change.

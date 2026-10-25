# ADR-0008: The import budget on a loaded machine

- Status: Proposed
- Date: 2026-10-18
- Deciders: Sanam Pakuwal
- Amends: ADR-0002 §7

## Context

ADR-0002 §7 set `import nepdate` under 5 ms and `import nepdate_patro` under 10 ms on a quiet
reference machine. ADR-0006 already replaced the CI check with a 50 ms ceiling, because a loaded
runner cannot hold 5 ms.

We measured the floor and the package with `-X importtime` on the reference machine, best of five,
with the CPU load sampled before each run. The bare interpreter is most of the cost:

| Import | Best us | Load, CPU % |
|---|---:|---:|
| `datetime` | 1510 | 59.0 |
| `enum` | 3418 | 65.9 |
| both | 4530 | 68.8 |

Before the deferral changes, seven alternating fresh-process runs gave a median of 22154 us for
`import nepdate` (mean load 74.2 %, range 41.9 to 90.8). After deferring the formatting, lenient
parser and fiscal label tables, the median was 19485 us (mean load 79.4 %, range 55.9 to 91.6).
Two pairs at about 90 % load were 24454 to 17849 us and 29785 to 20749 us. The package's own module
self time in those pairs fell from 11808 to 9284 us; `_format` and `_pattern` are no longer imported
at all, and `_parse` and `_fiscal` build less.

Later work put `_format` and `_pattern` back at import. A call-time `from ._format import ...` in
`__str__` and `long` is a module lookup on every call: on the same machine `str(d)` went from about
210 to 600 ns and `long(lang=Lang.NE)` (B5) from about 340 to 800 ns, against a 400 ns B5 target.
Their 1790 us of self time at about 90 % load is back in `import nepdate`, so the after numbers
above are better than the merged tree by about that much. Only the lenient parser and the fiscal
label strings stay deferred.

The best after-run was 13883 us at 65.5 % load, against the 4530 us floor at about the same load.
The remaining cost is CPython (`datetime`, `enum`), eight enum classes, the `NepaliDate` class body
and the 63 KB calendar table. None of those is removable without changing the public API or the
conversion design.

## Decision

1. The quiet-machine targets stay 5 ms for the core and 10 ms for the patro.
2. The measured budget on the reference machine is **15 ms for the core and 20 ms for the patro**,
   best of five `-X importtime` runs, with the load recorded. A run whose load is above 80 % CPU is
   reported next to the number and is not used for the budget check.
3. `benchmarks/import_time.py` and `docs/benchmarks.md` report both the numbers and the load.
   ADR-0006 gate 5 keeps its 50 ms gross-regression ceiling; it is not the budget check.
4. A future quiet-machine run that holds 5 ms and 10 ms replaces this ADR with one that says so.
   A run that cannot hold 15 ms and 20 ms is a regression and is reported, not tuned away.

## Consequences

- The 5 ms number in ADR-0002 §7 is no longer the number a loaded machine is judged against. The
  change is recorded here, not by editing the Accepted ADR.
- The budget is a ceiling for this Windows machine with Defender and the usual background services,
  not a claim that CPython can import a calendar library in 5 ms here.
- The deferral moves the lenient tables to the first `parse_lenient` call and builds the fiscal
  label strings per `FiscalYear.label(Lang.NE)` call. A deferral that puts an import on a
  benchmarked path (B1 to B8) is not taken; `tests/test_lazy_imports.py` pins which modules load
  with the package.

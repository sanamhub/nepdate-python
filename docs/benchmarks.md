# Benchmarks

The harness follows [`shared/spec/BENCHMARK.md`](../shared/spec/BENCHMARK.md): the 64 BS dates of
§2 and operations B1 to B8 of §3. All numbers are pyperf means in nanoseconds per single
operation. They were measured on 2026-10-18 on the reference machine, while the machine was
loaded: the load column is the CPU percent sampled around each pyperf process. This is a loaded
machine report, not a quiet-machine target run, and nothing was tuned for it.

## Machine

| Item | Value |
|---|---|
| CPU | 12th Gen Intel Core i5-12500H, 4 performance and 8 efficiency cores, 16 threads, 3.1 GHz |
| RAM | 31.7 GB |
| OS | Windows 11 Home 10.0.26300 |
| Power plan | Ultimate Performance |
| Affinity | logical CPU 2 (`--affinity 2`) |

## Versions

| Tool or package | Version |
|---|---|
| CPython | 3.13.14 (64-bit) |
| uv | 0.12.1 |
| pyperf | 2.10.0 |
| `nepdate-core` | 0.1.0 |
| `nepdate-patro` | 0.1.0 |
| `nepali-datetime` | 1.0.8.5 |
| `npdatetime` | 0.2.10 |
| `nepali` | 1.2.0 |
| `bikram-sambat` | 0.2.0 |
| `bikram` | 2.1.4 |
| `pyBSDate` | 0.3.2 |
| `nepali-calendar-utils` | 3.1.0 |
| `nepkit` | 0.4.1 |

## Command

```console
uv sync --group bench
uv run --group bench python benchmarks/run.py --date 2026-10-18
```

`run.py` starts one pyperf process per benchmark, pinned by pyperf's `--affinity 2`, and samples
the CPU load every 0.5 s while it runs. The per-process command is:

```console
.venv\Scripts\python.exe benchmarks\bench.py --only b1 -o benchmarks\results\2026-10-18\b1.json --rigorous --quiet
```

`benchmarks/results/2026-10-18/` holds the pyperf JSON, `summary.json`, `probe.json`,
`import_time.json` and `bytes.json`.

## B1 to B8

The `bytes/op` column is tracemalloc retained bytes per result over 10,000 calls whose results
are kept in a list. It is not the same measure as .NET's Allocated, and it is not a timing
measurement. The C# column is the .NET 10 column of the hub's `docs/benchmarks/dotnet.md`.

| ID | Operation | This port ns/op | stdev | Load, CPU % mean (min to max) | Target ns/op | Met? | bytes/op | C# .NET 10 ns/op |
|---|---|---:|---:|---|---:|---|---:|---:|
| B1 | BS to AD | 724.4 | 115.7 | 31.5 (8.5 to 100.0) | 550 | no | 40.6 | 13.29 |
| B2 | AD to BS | 821.6 | 175.3 | 66.1 (23.2 to 100.0) | 450 | no | 104.6 | 18.64 |
| B3 | add 1000 days | 662.4 | 77.1 | 50.6 (18.9 to 89.8) | 400 | no | 104.6 | 17.50 |
| B4 | add 13 months, clamp | 597.7 | 79.8 | 50.3 (14.0 to 100.0) | 350 | no | 136.6 | 18.85 |
| B5 | long, Nepali, weekday | 526.8 | 100.4 | 37.4 (14.1 to 97.2) | 400 | no | 110.2 | 153.02 |
| B6 | strict parse | 1316.3 | 201.6 | 33.5 (15.8 to 98.4) | 1000 | no | 132.6 | 21.55 |
| B7 | patro info | 128.3 | 9.1 | 21.1 (9.7 to 35.5) | 150 | yes | 8.6 | 47.93 |
| B8 | patro month grid | 21608.9 | 5693.3 | 51.9 (7.6 to 95.2) | 9000 | no | 320.6 | 3133 |

B8 measures `[info(x) for x in DateRange.month(d.year, d.month)]` for each of the 64 patro
dates, so it is 64 month grids per iteration.

## Competitors: B1, BS to AD

`n/64` is the number of BENCHMARK dates the package accepted. `matches` is how many of those
results equal the committed `shared/data` table (counts and every rejected or differing date are in
`benchmarks/results/2026-10-18/probe.json`; the dates are tabulated in
[`competitors.md`](competitors.md)). A package below 64 on either count is never ranked.

| Package | ns/op | n/64 | matches | Load, CPU % mean (min to max) |
|---|---:|---:|---:|---|
| `nepdate-core` | 724.4 | 64/64 | 64 | 31.5 (8.5 to 100.0) |
| `bikram-sambat` | 1244.8 | 64/64 | 61 | 37.5 (10.7 to 80.2) |
| `nepkit` | 2106.4 | 64/64 | 62 | 33.8 (8.0 to 81.2) |
| `nepali-datetime` | 2618.4 | 64/64 | 62 | 40.6 (11.4 to 97.4) |
| `npdatetime` | 6104.7 | 64/64 | 62 | 63.6 (16.4 to 99.8) |
| `pyBSDate` | 7886.7 | 64/64 | 60 | 66.7 (22.5 to 100.0) |
| `nepali` | 15477.7 | 64/64 | 61 | 57.9 (13.4 to 100.0) |
| `bikram` | 18192.4 | 63/64 | 62 | 73.0 (9.1 to 100.0) |
| `nepali-calendar-utils` | 76786.6 | 64/64 | 61 | 48.2 (18.8 to 89.2) |

## Competitors: B2, AD to BS

| Package | ns/op | n/64 | matches | Load, CPU % mean (min to max) |
|---|---:|---:|---:|---|
| `nepdate-core` | 821.6 | 64/64 | 64 | 66.1 (23.2 to 100.0) |
| `bikram-sambat` | 1103.2 | 64/64 | 61 | 92.6 (39.8 to 100.0) |
| `nepkit` | 2089.4 | 64/64 | 62 | 52.7 (17.3 to 98.6) |
| `npdatetime` | 3953.0 | 64/64 | 62 | 41.3 (17.7 to 83.9) |
| `nepali` | 7366.0 | 63/64 | 60 | 58.9 (10.4 to 100.0) |
| `nepali-datetime` | 8496.8 | 64/64 | 62 | 50.9 (8.8 to 88.8) |
| `pyBSDate` | 10671.7 | 64/64 | 62 | 83.8 (25.4 to 100.0) |
| `nepali-calendar-utils` | 52465.1 | 64/64 | 61 | 27.4 (13.8 to 59.7) |
| `bikram` | 72847.3 | 62/64 | 62 | 66.2 (8.4 to 100.0) |

`npdatetime` is a Rust/PyO3 extension, not pure Python. The other seven are pure Python. B3 to B8
have no call with the same signature and overflow rules in these packages, so they are `n/a`.

Every competitor rejects or differs from `shared/data` on 2 to 4 of the 64 dates, so none can be ranked
against this port for the BENCHMARK §6 target, and the target is met by default. A difference is a
disagreement with the committed table, not proof that the other package is wrong: years 2087 to
2090 are questionable in NepDate's own data too (`docs/competitors.md`). This is not a speed
claim. The numbers above still show where each package would land.

## Import time

Best of five `-X importtime` runs, with the load sampled before each run. The first table is the
P5 measurement against the old 5 ms target.

| Import | Best us | Samples, us | Load, CPU % mean (min to max) |
|---|---:|---|---|
| `import nepdate` | 15086 | 46715, 25968, 27548, 15086, 23354 | 69.8 (56.9 to 91.1) |
| `import nepdate` then `import nepdate_patro` | 8253 | 8745, 11410, 8253, 8890, 11649 | 64.4 (40.6 to 76.1) |

P6 first deferred the formatting, lenient parser and fiscal label tables. The before and after runs below
alternate between a copy of `main` at `31a994f` on `PYTHONPATH` and this branch, seven fresh
processes each, so load drift affects both sides.

| Tree | Best us | Median us | Mean us | Load, CPU % mean (min to max) |
|---|---:|---:|---:|---|
| Before | 14294 | 22154 | 21372 | 74.2 (41.9 to 90.8) |
| After | 13883 | 19485 | 18406 | 79.4 (55.9 to 91.6) |

At about 90 % load the pairs were 24454 to 17849 us and 29785 to 20749 us. The package's own module
self time in the first pair fell from 11808 to 9284 us: `_format` (1160 us) and `_pattern` (630 us)
are no longer imported by `import nepdate`, and `_parse` (886 to 530 us) and `_fiscal` (999 to
656 us) build less.

Review restored `_format` and `_pattern` at import: importing them inside `__str__` and `long`
cost a module lookup per call, about 210 to 600 ns for `str(d)` and 340 to 800 ns for B5 on this
machine. The after row above therefore includes about 1790 us (at about 90 % load) that the merged
tree pays again; only the lenient parser and the fiscal labels stay deferred.

The floor is the bare interpreter, measured in the same loaded window:

| Import | Best us | Load, CPU % |
|---|---:|---:|
| `datetime` | 1510 | 59.0 |
| `enum` | 3418 | 65.9 |
| both | 4530 | 68.8 |

ADR-0008 proposes a load-aware budget of 15 ms for the core and 20 ms for the patro, best of five
at up to 80 % CPU, while the quiet-machine targets stay 5 ms and 10 ms. Until ADR-0008 is accepted,
the 5 ms number in ADR-0002 §7 is still the published target, and the loaded numbers above miss it.
The gate's 50 ms ceiling passes (ADR-0006).

## P7 quiet window

P7 checked the load before measuring anything. The 2026-10-18 session made 19 `--check-load`
samples and found no window. The 2026-10-21 session made 17 samples between 06:24:23 and 07:05:59.
The all-CPU load ranged from 1.9 to 87.9 % (mean 26.7 %); 8 samples were under the 15 % limit. The
usable window was 06:45:48 to 06:49:12. The attempts are in
`benchmarks/results/2026-10-21/quiet.json`.

The import measurement ran inside that window. A sample at or above 15 % was retried, and only the
five quiet samples per import count. The JSON is
`benchmarks/results/2026-10-21/import_time.json`.

| Import | Best us | Samples, us | Load, CPU % mean (min to max) |
|---|---:|---|---|
| `import nepdate` | 5825 | 6417, 5938, 6439, 5825, 6611 | 6.3 (1.0 to 14.9) |
| `import nepdate` then `import nepdate_patro` | 3499 | 4240, 3527, 3538, 3499, 3755 | 5.7 (1.1 to 10.3) |
| `import datetime, enum` | 1814 | 1868, 1814, 1820, 1844, 1848 | 5.7 (1.0 to 14.8) |

The best separate `-X importtime` captures were 6170 us for the core and 4134 us for the patro.
Their self times, in us:

| Module | Self us |
|---|---:|
| `nepdate._names` | 738 |
| `nepdate._calendar` | 496 |
| `nepdate` | 462 |
| `nepdate._date` | 409 |
| `nepdate._format` | 394 |
| `nepdate._errors` | 290 |
| `nepdate._fiscal` | 220 |
| `nepdate._parse` | 210 |
| `nepdate._range` | 210 |
| `nepdate._diff` | 203 |
| `enum` | 1390 |
| `nepdate_patro._tables` | 1182 |
| `nepdate_patro` | 2953 |

The quiet core 5825 us misses the 5 ms target and meets the proposed 15 ms budget. The patro
3499 us holds both the 10 ms target and the proposed 20 ms budget. The decision therefore leaves
ADR-0008 Proposed and records the numbers for the owner; no new ADR was written.

The B1 to B8 batch started at 11.1 % but did not stay quiet. `b1`, `b3`, `b4`, `b5`, `b7` and
`b8` crossed the 15 % background limit; `b7` reached 89.2 %. Only `b2` and `b6` are unloaded, so
the batch is not a verdict. The loaded batch summary is in
`benchmarks/results/2026-10-21/summary.json`. No P7 B1 to B8 table and no C# column are published,
and the B1 to B8 work and the miss profiles stay pending.

## Targets

The ADR-0002 §8 targets are B1 under 550 ns, B2 under 450, B3 under 400, B4 under 350, B5 under
400, B6 under 1000, B7 under 150 and B8 under 9000. On this loaded machine the measured numbers
are higher than the prototype numbers in ADR-0002. The table says which targets were met here;
it is not a quiet-machine result. P5 reports the miss rather than tuning the machine or the code.

A `timeit` check at a lower load gave B7 136.5 ns and B8 19238 ns, so B7 crosses the 150 ns target
when the machine is quieter and B8 remains about 2.1 times the 9000 ns target. The pyperf numbers
above are the published ones because they come from the BENCHMARK protocol and carry the load.

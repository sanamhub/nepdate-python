# Benchmarks

The harness follows [`shared/spec/BENCHMARK.md`](../shared/spec/BENCHMARK.md): the 64 BS dates of
section 2 and operations B1 to B8 of section 3. All numbers are pyperf means in nanoseconds per
single operation. They were measured on 2026-11-02 on the reference machine. The machine was
partly loaded: the load columns are in `benchmarks/results/2026-11-02/summary.json`, and most rows
are marked `loaded`. B8 is final; the other rows are kept as indicative, not as quiet-machine target
verdicts.

## Machine

| Item | Value |
|---|---|
| CPU | 12th Gen Intel Core i5-12500H, 4 performance and 8 efficiency cores, 16 threads, 3.1 GHz |
| RAM | 31.7 GB |
| OS | Windows 11 Home 10.0.26300 |
| Power plan | Ultimate Performance |
| Affinity | logical CPU 2 (`--affinity 2`) |
| Load before | 1, 4 and 14 percent, sampled 2 s apart |
| Load after | 5, 23 and 5 percent, sampled 2 s apart |

The machine had the owner's normal desktop applications open. No other build, test suite or
benchmark ran during the run.

## Versions

| Tool or package | Version |
|---|---|
| CPython | 3.12.13 (64-bit) |
| uv | 0.12.1 |
| pyperf | 2.10.0 |
| `nepdate-core` | 0.1.0rc1 |
| `nepdate-patro` | 0.1.0rc1 |
| `nepali-datetime` | 1.0.8.5 |
| `nepali` | 1.2.0 |

## Command

```console
uv sync --all-packages --group bench
uv run --all-packages --group bench python benchmarks/run.py --date 2026-11-02 --allow-loaded
```

`run.py` starts one pyperf process per benchmark, pinned by pyperf's `--affinity 2`, and samples
the CPU load every 0.5 s while it runs. The per-process command is:

```console
.venv\Scripts\python.exe benchmarks\bench.py --only b1 -o benchmarks\results\2026-11-02\b1.json --rigorous --quiet
```

The raw results are in [`benchmarks/results/2026-11-02/`](../benchmarks/results/2026-11-02/), with
`summary.json` and one JSON per benchmark. The console log is `docs/raw/2026-11-02-py.log`.

## Results

Time is the pyperf mean per single operation, with its standard deviation. The C# column is the
.NET 10 column of the hub's
[`docs/benchmarks/dotnet.md`](https://github.com/sanamhub/nepdate/blob/main/docs/benchmarks/dotnet.md),
run on the same machine on 2026-11-02. Python and TypeScript report allocations as "not measured";
the harness has no reliable allocator count for CPython.

| ID | Operation | nepdate ns/op | std ns | C# .NET 10 ns/op | C# bytes/op |
|---|---|---:|---:|---:|---:|
| B1 | BS to AD | 671.20 | 8.26 | 13.50 | 0 |
| B2 | AD to BS | 569.87 | 24.48 | 20.10 | 0 |
| B3 | add 1000 days | 517.52 | 6.93 | 19.05 | 0 |
| B4 | add 13 months, Clamp | 472.77 | 9.17 | 20.19 | 0 |
| B5 | long format, Nepali, weekday | 476.40 | 10.67 | 150.41 | 435 |
| B6 | strict parse `YYYY/MM/DD` | 1,261.36 | 21.38 | 22.42 | 0 |
| B7 | patro info | 130.58 | 2.10 | 48.21 | 51 |
| B8 | patro month grid | 17,178.66 | 171.35 | 3,112.76 | 1,429 |

## Competitors (B1 and B2)

| Package | B1 ns/op | B1 agrees | B2 ns/op | B2 agrees |
|---|---:|---|---:|---|
| `nepali-datetime` | 2,043.93 | no (62 of 64) | 6,613.95 | no (62 of 64) |
| `nepali` | 12,457.04 | no (61 of 64) | 6,545.16 | no (60 of 64) |

NepDate is faster than both on both conversions. `nepali-datetime` is the closest at 3.05 times
NepDate on B1 and 11.6 times on B2. `nepali` is 18.6 times slower on B1 and 11.5 times on B2.

The 64-date agreement counts come from `bench.py --probe`; the full mismatch lists are in
`benchmarks/results/2026-11-02/probe.json`. `nepali-datetime` differs at BS 2088-01-04 and
2089-06-10 in both directions. `nepali` differs at 2085, 2088 and 2089, and rejects the AD
1943-04-14 input.

## Target

BENCHMARK section 6 asks for the fastest pure-Python option among the competitors. NepDate is
faster than `nepali-datetime`, the closest pure-Python package, on B1, B2 and B7 even in this loaded
run. Passes.

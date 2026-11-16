# Benchmarks

The harness follows [`shared/spec/BENCHMARK.md`](../shared/spec/BENCHMARK.md): the 64 BS dates of
section 2 and operations B1 to B8 of section 3. All numbers are pyperf means in nanoseconds per
single operation. They were measured on 2026-11-16 on the reference machine, which was idle. The
load of every row is in `benchmarks/results/2026-11-16/summary.json`, and no row is marked
`loaded`.

## Machine

| Item | Value |
|---|---|
| CPU | 12th Gen Intel Core i5-12500H, 4 performance and 8 efficiency cores, 16 threads, 3.1 GHz |
| RAM | 31.7 GB |
| OS | Windows 11 Home 10.0.26300 |
| Power plan | Ultimate Performance |
| Affinity | logical CPU 2 (`--affinity 2`) |
| Idle gate before the run | 4.1 percent average, 15.3 peak (30 one-second samples) |
| Load during the full run | 10.8 percent average, 30.2 peak over 443 one-second samples; 5.6 and 27.0 on the CPUs other than CPU 2 |

The machine was idle: no other build, test suite or benchmark ran during the run. Three competitor
rows (`nepali` B1, `nepali-datetime` B2 and `nepali` B2) were marked `loaded` by the harness in the
full run, because of short bursts of background load while they ran. They were rerun with `--only`
until each ran quiet, and the table uses those reruns; the other nine rows are from the full run.
The samples are in
[`benchmarks/results/2026-11-16/cpu-samples.txt`](../benchmarks/results/2026-11-16/cpu-samples.txt)
and `cpu-samples-rerun-b1-nepali.txt`.

## Versions

| Tool or package | Version |
|---|---|
| CPython | 3.12.13 (64-bit) |
| uv | 0.12.1 |
| pyperf | 2.10.0 |
| `nepdate-core` | 1.0.0rc1 |
| `nepdate-patro` | 1.0.0rc1 |
| `nepali-datetime` | 1.0.8.5 |
| `nepali` | 1.2.0 |

## Command

```console
uv sync --all-packages --group bench
uv run --all-packages --group bench python benchmarks/run.py --date 2026-11-16
uv run --all-packages --group bench python benchmarks/run.py --date 2026-11-16 --only b1:nepali --only b2:nepali-datetime --only b2:nepali
```

`run.py` starts one pyperf process per benchmark, pinned by pyperf's `--affinity 2`, and samples
the CPU load every 0.5 s while it runs. The per-process command is:

```console
.venv\Scripts\python.exe benchmarks\bench.py --only b1 -o benchmarks\results\2026-11-16\b1.json --rigorous --quiet
```

The raw results are in [`benchmarks/results/2026-11-16/`](../benchmarks/results/2026-11-16/), with
`summary.json` and one JSON per benchmark. The console log is `docs/raw/2026-11-16-py.log`.

## Results

Time is the pyperf mean per single operation, with its standard deviation. The C# column is the
.NET 10 column of the hub's
[`docs/benchmarks/dotnet.md`](https://github.com/sanamhub/nepdate/blob/main/docs/benchmarks/dotnet.md),
run on the same machine on 2026-11-16. Python and TypeScript report allocations as "not measured";
the harness has no reliable allocator count for CPython.

| ID | Operation | nepdate ns/op | std ns | C# .NET 10 ns/op | C# bytes/op |
|---|---|---:|---:|---:|---:|
| B1 | BS to AD | 612.77 | 4.22 | 13.27 | 0 |
| B2 | AD to BS | 518.85 | 6.95 | 18.70 | 0 |
| B3 | add 1000 days | 474.25 | 4.78 | 20.06 | 0 |
| B4 | add 13 months, Clamp | 431.25 | 3.35 | 19.30 | 0 |
| B5 | long format, Nepali, weekday | 433.35 | 3.48 | 139.04 | 435 |
| B6 | strict parse `YYYY/MM/DD` | 1,157.10 | 9.52 | 21.13 | 0 |
| B7 | patro info | 118.91 | 1.11 | 48.63 | 51 |
| B8 | patro month grid | 15,840.07 | 135.79 | 3,274.50 | 1,429 |

## Competitors (B1 and B2)

| Package | B1 ns/op | B1 agrees | B2 ns/op | B2 agrees |
|---|---:|---|---:|---|
| `nepali-datetime` | 1,888.81 | no (62 of 64) | 6,152.13 | no (62 of 64) |
| `nepali` | 11,540.27 | no (61 of 64) | 6,125.01 | no (60 of 64) |

NepDate is faster than both on both conversions. `nepali-datetime` is the closest at 3.08 times
NepDate on B1 and 11.9 times on B2. `nepali` is 18.8 times slower on B1 and 11.8 times on B2.

The 64-date agreement counts come from `bench.py --probe`; the full mismatch lists are in
`benchmarks/results/2026-11-16/probe.json`. `nepali-datetime` differs at BS 2088-01-04 and
2089-06-10 in both directions. `nepali` differs at 2085, 2088 and 2089, and rejects the AD
1943-04-14 input.

## Target

BENCHMARK section 6 asks for the fastest pure-Python option among the competitors. NepDate is
faster than `nepali-datetime`, the closest pure-Python package, on B1 and B2 in this quiet run.
Passes.

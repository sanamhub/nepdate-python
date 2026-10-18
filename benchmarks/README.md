# Benchmarks

The harness follows [`shared/spec/BENCHMARK.md`](../shared/spec/BENCHMARK.md): the 64 BS dates of
§2, B1 to B8 of §3, and the 64 patro dates of §3 for B7 and B8. Times are pyperf means in
nanoseconds per single operation, with the machine load measured next to every number.

## Inputs

`inputs.py` holds the 64 core dates, their AD dates and their `YYYY/MM/DD` text, plus the 64 patro
dates. The literals are committed. `computed_bs`, `computed_ad`, `computed_text` and
`computed_patro` recompute them from `src/nepdate/_calendar.py` and the patro coverage, and
`scripts/tests/test_benchmark_inputs.py` checks that both agree.

## Commands

```console
uv sync --group bench
uv run --group bench python benchmarks/run.py --date YYYY-MM-DD
```

`run.py` starts one pyperf process per benchmark, pinned to logical CPU 2 with pyperf's
`--affinity 2`, samples the CPU load while it runs, and writes `benchmarks/results/<date>/`. The
per-benchmark JSON files come from pyperf; `summary.json` has the times, the load and the
competitor counts. `benchmarks/bench.py --only b7` runs one benchmark by hand.

`run.py --check-load` samples the all-CPU and logical-CPU-2 load without importing a competitor,
appends the sample to `quiet.json` and exits 1 when the all-CPU load is 15 % or more. A normal run
stops with exit 3 above 15 % unless `--allow-loaded` is given. Every row records `load_before`,
`loaded` and the load range while the process ran; a row with `loaded: true` is not a target
verdict (P7).

Each benchmark function walks all its inputs and returns the result list; pyperf divides by
`inner_loops`, the number of accepted inputs, so the reported value is per single operation. A
competitor that rejects some dates is timed only on the ones it accepts and shown as `n/64`.

## Calls

| Package | B1 BS to AD | B2 AD to BS |
|---|---|---|
| `nepdate-core` | `NepaliDate(y, m, d).to_date()` | `NepaliDate.from_date(ad)` |
| `nepali-datetime` | `nepali_datetime.date(y, m, d).to_datetime_date()` | `nepali_datetime.date.from_datetime_date(ad)` |
| `npdatetime` | `npdatetime.NepaliDate(y, m, d).to_gregorian()` | `npdatetime.NepaliDate.from_gregorian(y, m, d)` |
| `nepali` | `converter.nepali_to_english(y, m, d)` | `converter.english_to_nepali(y, m, d)` |
| `bikram-sambat` | `bikram_sambat.conversion.bs_to_ad(y, m, d)` | `bikram_sambat.conversion.ad_to_bs(ad)` |
| `bikram` | `bikram.convert_bs_to_ad(bikram.samwat(y, m, d))` | `bikram.convert_ad_to_bs(ad)` |
| `pyBSDate` | `pyBSDate.convert_BS_to_AD(y, m, d)` | `pyBSDate.convert_AD_to_BS(y, m, d)` |
| `nepali-calendar-utils` | `NepaliDateConverter.convert_nepali_to_english(y, m, d)` | `NepaliDateConverter.convert_english_to_nepali(y, m, d)` |
| `nepkit` | `nepkit.bs_to_ad(nepkit.BSDate(y, m, d))` | `nepkit.ad_to_bs(ad)` |

The result is normalised to `(year, month, day)`; an object with those three attributes is
unpacked. `npdatetime` is a Rust/PyO3 extension, not pure Python, and is reported separately.

B3 to B6 have no call with the same signature and overflow rules in these eight packages, so the
competitor columns are `n/a`. B7 and B8 are patro operations and only this port has them.

## Agreement

`bench.py --probe` calls every competitor on all 64 dates in both directions and compares the
result with the committed data. `agrees` is true only when all 64 B1 results and all 64 B2 results
match. Each direction also lists every rejected or differing date with the input, the competitor's
result and ours; `docs/competitors.md` tabulates them. A package that is fast but wrong is listed,
never ranked.

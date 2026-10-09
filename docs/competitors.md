# Other Python packages for the Bikram Sambat calendar

Checked 2026-09-25 against PyPI metadata, pepy.tech / pypistats, GitHub and the sources (no package
installed); versions, licences, dependencies and wheels rechecked against the PyPI JSON API on
2026-10-08 (no changes except the `npdatetime` and `nepkit` notes below). Used by task P5-02 (benchmarks). Every package is pure Python with a lookup table,
except `npdatetime` (Rust/PyO3). Only `bikram-sambat` covers 1901–2199 (its data came from
NepDate).

## Packages we benchmark against

| Package (import) | Version | Downloads 30 d / total | License | BS range | Notes |
|---|---|---|---|---|---|
| `nepali-datetime` (`nepali_datetime`) | 1.0.8.5 (2026-05) | 23.5k / 526k | PyPI says MIT, repo says Apache-2.0 | 1975–2100 | market leader; clones `datetime`; parses a CSV with `open()` at import; `.pyi` but no `py.typed` |
| `npdatetime` | 0.2.10 (2026-08) | 9.4k / 79k | MIT | 1975–2100 | Rust/PyO3 0.21; 21 wheels, CPython 3.8 to 3.14 on only 3 platforms (Windows x64, Linux x64 glibc 2.34+, macOS arm64); no sdist, no musllinux, no free-threaded build |
| `nepali` (py-nepali) | 1.2.0 (2026-02) | 1.6k / 130k | MIT | 2000–2099 | loops year by year |
| `bikram-sambat` (`bikram_sambat`) | 0.2.0 (2026-04) | 875 / 11k | MIT | 1901–2199 | depends on `pytz`; table differs from NepDate `main` in 12 years |
| `bikram` | 2.1.4 (2025-10) | 608 / 40k | MIT | 2000–2089 | walks month by month |
| `pyBSDate` | 0.3.2 (2025-04) | 278 / 32k | MIT | 1970–2100 | 2063 anchor bug: every BS 2063 date is a year off |
| `nepali-calendar-utils` | 3.1.0 (2026-09) | 919 / 5.8k | MPL-2.0 | 1970–2100 | very active; events, holidays, working days |
| `nepkit` | 0.4.1 (2026-09) | 1.0k / 2.5k | MIT | 2000–2090 | typed; depends on typer and rich (CLI), plus pyreadline3 and tzdata on Windows; Python 3.12+ |

Calls to benchmark (normalise to integers in, `datetime.date` or tuple out):

| Package | BS → AD | AD → BS |
|---|---|---|
| nepali-datetime | `nepali_datetime.date(y, m, d).to_datetime_date()` | `nepali_datetime.date.from_datetime_date(dt)` |
| npdatetime | `npdatetime.NepaliDate(y, m, d).to_gregorian()` | `NepaliDate.from_gregorian(y, m, d)` |
| nepali | `nepali.date_converter.converter.nepali_to_english(y, m, d)` | `converter.english_to_nepali(y, m, d)` |
| bikram-sambat | `bikram_sambat.conversion.bs_to_ad(y, m, d)` | `conversion.ad_to_bs(dt)` |
| bikram | `bikram.convert_bs_to_ad(bikram.samwat(y, m, d))` | `bikram.convert_ad_to_bs(dt)` |
| pyBSDate | `pyBSDate.convert_BS_to_AD(y, m, d)` | `pyBSDate.convert_AD_to_BS(y, m, d)` |
| nepali-calendar-utils | `NepaliDateConverter.convert_nepali_to_english(y, m, d)` | `NepaliDateConverter.convert_english_to_nepali(y, m, d)` |
| nepkit | `nepkit.bs_to_ad(nepkit.BSDate(y, m, d))` | `nepkit.ad_to_bs(dt)` |

## Correctness (why the table needs an "agrees" column)

AD date of each BS New Year compared with NepDate: `nepali-datetime` differs in 6 years (2088, 2089,
2090, 2092, 2096, 2097) and in month lengths in 17 years; `nepali` in 4 (2085, 2088–2090);
`pyBSDate` in 8 (including 1975 and the 2063 bug); `nepali-calendar-utils` in month lengths of 12
years. 2087–2090 is also where NepDate's own data is questionable (`shared/data/README.md`).

## Not benchmarked

Stale or abandoned: `nepalicalendar` (2016, Python 2 era, has tithi and events), `nepali-date`
(2020, superseded by nepali-datetime), `ad-bs-converter` (AD→BS only, data ends in AD 2026, runtime
deps on pydantic and twine), `nepali-date-utils` (GPL-3.0, 2024), `nepali-date-converter` (2023,
wraps nepali-datetime), `adbs` (2016, locale-dependent names), `datetime-nepali` (fork).

## Measured prototype (research, not our code)

The design prototype's numbers on the reference machine are in ADR-0002 ("Measurements"): on
CPython 3.13, B1 492.6 ns and B2 388.2 ns over the 64 BENCHMARK dates. No competitor has been timed
yet; P5-02 does that in the same harness. A PyO3 call would still pay 60 to 150 ns for argument
parsing and object creation, so a native build would be about 1.5 to 3 times faster per call, not
100 times (ADR-0002).

## Native or platform support

None. The standard library (`datetime`, `calendar`, `zoneinfo`) has no Bikram Sambat calendar.
`PyICU` and `babel` follow ICU and CLDR, whose calendar types include no Nepali calendar (ICU
calendar list: https://unicode-org.github.io/icu/userguide/datetime/calendar/; hub brief of
2026-10-07, not rechecked online on 2026-10-08). The packages above are third-party tables, and none agrees with `shared/data` on
every year. So the port is needed.

## Name

Checked 2026-10-06 and again 2026-10-08: `nepdate` on PyPI is taken by "Gets today's nepali date" (Samir Maharjan,
versions 0.0.2 to 0.0.4, all uploaded on 2021-09-22, no repository link). Free: `nepdate-bs`,
`pynepdate`. `nepdate` is free on npm and crates.io. The patro distribution name `nepdate-patro`
(ADR-0001) and `nepdate-bs` both returned 404 from the PyPI JSON API on 2026-10-08 (free); P0-06
registers `nepdate-patro`, and `nepdate-bs` if the human picks option 2 below, as pending publishers.

Options (human decision, P0-06):
1. Ask the owner to transfer the name; if there is no answer, file a PEP 541 request on
   `pypi/support` (abandoned project). Slow: allow months.
2. Publish as `nepdate-bs` (import `nepdate`) now, and move to `nepdate` later if the transfer
   succeeds, leaving `nepdate-bs` as a thin package that depends on it.
   `nepdate-patro` then changes its dependency from `nepdate-bs` to `nepdate` in the same
   release.

The import name stays `nepdate` either way. Installing both this and the old package would clash
on that import name; the old one has no users worth counting, so this is accepted.

## Sources

PyPI JSON API (`https://pypi.org/pypi/<name>/json`), https://pepy.tech, https://pypistats.org,
and the repositories: amitgaru/nepali-datetime, 4mritGiri/npdatetime, opensource-nepal/py-nepali,
ashok095/bikram-sambat, aerawatcorp/bikram, SushilShrestha/pyBSDate,
shivathapaa/nepali_calendar_utils, akakritagya/nepkit (all on GitHub).

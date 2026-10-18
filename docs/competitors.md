# Other Python packages for the Bikram Sambat calendar

Checked 2026-09-25 against PyPI metadata, pepy.tech / pypistats, GitHub and the sources (no package
installed); versions, licences, dependencies and wheels rechecked against the PyPI JSON API on
2026-10-08 (no changes except the `npdatetime` and `nepkit` notes below). Used by the benchmark
suite. Every package is pure Python with a lookup table,
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

### Dates rejected or different

Each row is one of the 64 BENCHMARK dates where the package raised or returned a date other than
the committed table. `rejected` means the call raised. The last column is `yes` when the Bikram
Sambat year is 2087, 2088, 2089 or 2090; for BS to AD that is the input year, for AD to BS it is
our expected BS year. These are disagreements with the committed table, not proof that the other
package is wrong, and they are not a ranking.

| Package | Direction | Input | Theirs | Ours | 2087 to 2090 |
|---|---|---|---|---|---|
| `nepali-datetime` | BS to AD | 2088-01-04 | 2031-04-18 | 2031-04-19 | yes |
| `nepali-datetime` | BS to AD | 2089-06-10 | 2032-09-26 | 2032-09-27 | yes |
| `nepali-datetime` | AD to BS | 2031-04-19 | 2088-01-05 | 2088-01-04 | yes |
| `nepali-datetime` | AD to BS | 2032-09-27 | 2089-06-11 | 2089-06-10 | yes |
| `npdatetime` | BS to AD | 2088-01-04 | 2031-04-18 | 2031-04-19 | yes |
| `npdatetime` | BS to AD | 2089-06-10 | 2032-09-26 | 2032-09-27 | yes |
| `npdatetime` | AD to BS | 2031-04-19 | 2088-01-05 | 2088-01-04 | yes |
| `npdatetime` | AD to BS | 2032-09-27 | 2089-06-11 | 2089-06-10 | yes |
| `nepali` | BS to AD | 2086-07-23 | 2029-11-09 | 2029-11-08 | no |
| `nepali` | BS to AD | 2088-01-04 | 2031-04-17 | 2031-04-19 | yes |
| `nepali` | BS to AD | 2089-06-10 | 2032-09-26 | 2032-09-27 | yes |
| `nepali` | AD to BS | 1943-04-14 | rejected | 2000-01-01 | no |
| `nepali` | AD to BS | 2029-11-08 | 2086-07-22 | 2086-07-23 | no |
| `nepali` | AD to BS | 2031-04-19 | 2088-01-06 | 2088-01-04 | yes |
| `nepali` | AD to BS | 2032-09-27 | 2089-06-11 | 2089-06-10 | yes |
| `bikram-sambat` | BS to AD | 2086-07-23 | 2029-11-09 | 2029-11-08 | no |
| `bikram-sambat` | BS to AD | 2088-01-04 | 2031-04-17 | 2031-04-19 | yes |
| `bikram-sambat` | BS to AD | 2089-06-10 | 2032-09-26 | 2032-09-27 | yes |
| `bikram-sambat` | AD to BS | 2029-11-08 | 2086-07-22 | 2086-07-23 | no |
| `bikram-sambat` | AD to BS | 2031-04-19 | 2088-01-06 | 2088-01-04 | yes |
| `bikram-sambat` | AD to BS | 2032-09-27 | 2089-06-11 | 2089-06-10 | yes |
| `bikram` | BS to AD | 2000-01-01 | 1944-01-02 | 1943-04-14 | no |
| `bikram` | BS to AD | 2090-11-24 | rejected | 2034-03-08 | yes |
| `bikram` | AD to BS | 1943-04-14 | rejected | 2000-01-01 | no |
| `bikram` | AD to BS | 2034-03-08 | rejected | 2090-11-24 | yes |
| `pyBSDate` | BS to AD | 2063-06-22 | 2005-10-08 | 2006-10-08 | no |
| `pyBSDate` | BS to AD | 2086-07-23 | 2029-11-09 | 2029-11-08 | no |
| `pyBSDate` | BS to AD | 2088-01-04 | 2031-04-18 | 2031-04-19 | yes |
| `pyBSDate` | BS to AD | 2090-11-24 | 2034-03-09 | 2034-03-08 | yes |
| `pyBSDate` | AD to BS | 2029-11-08 | 2086-07-22 | 2086-07-23 | no |
| `pyBSDate` | AD to BS | 2031-04-19 | 2088-01-05 | 2088-01-04 | yes |
| `nepali-calendar-utils` | BS to AD | 2086-07-23 | 2029-11-09 | 2029-11-08 | no |
| `nepali-calendar-utils` | BS to AD | 2088-01-04 | 2031-04-17 | 2031-04-19 | yes |
| `nepali-calendar-utils` | BS to AD | 2089-06-10 | 2032-09-26 | 2032-09-27 | yes |
| `nepali-calendar-utils` | AD to BS | 2029-11-08 | 2086-07-22 | 2086-07-23 | no |
| `nepali-calendar-utils` | AD to BS | 2031-04-19 | 2088-01-06 | 2088-01-04 | yes |
| `nepali-calendar-utils` | AD to BS | 2032-09-27 | 2089-06-11 | 2089-06-10 | yes |
| `nepkit` | BS to AD | 2088-01-04 | 2031-04-18 | 2031-04-19 | yes |
| `nepkit` | BS to AD | 2089-06-10 | 2032-09-26 | 2032-09-27 | yes |
| `nepkit` | AD to BS | 2031-04-19 | 2088-01-05 | 2088-01-04 | yes |
| `nepkit` | AD to BS | 2032-09-27 | 2089-06-11 | 2089-06-10 | yes |

## Not benchmarked

Stale or abandoned: `nepalicalendar` (2016, Python 2 era, has tithi and events), `nepali-date`
(2020, superseded by nepali-datetime), `ad-bs-converter` (AD→BS only, data ends in AD 2026, runtime
deps on pydantic and twine), `nepali-date-utils` (GPL-3.0, 2024), `nepali-date-converter` (2023,
wraps nepali-datetime), `adbs` (2016, locale-dependent names), `datetime-nepali` (fork).

## Measured prototype (research, not our code)

The design prototype's numbers on the reference machine are in ADR-0002 ("Measurements"): on
CPython 3.13, B1 492.6 ns and B2 388.2 ns over the 64 BENCHMARK dates. No competitor has been timed
yet; the benchmark suite does that in the same harness. A PyO3 call would still pay 60 to 150 ns for argument
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
(ADR-0001) and `nepdate-bs` both returned 404 from the PyPI JSON API on 2026-10-08 (free); the chosen
core name is `nepdate-core` (ADR-0007).

Options (considered before the first release):
1. Ask the owner to transfer the name; if there is no answer, file a PEP 541 request on
   `pypi/support` (abandoned project). Slow: allow months.
2. Publish as `nepdate-bs` (import `nepdate`) now, and move to `nepdate` later if the transfer
   succeeds, leaving `nepdate-bs` as a thin package that depends on it.
   `nepdate-patro` then changes its dependency from `nepdate-bs` to `nepdate` in the same
   release.

On 2026-10-18 the owner chose neither: the core is published as `nepdate-core` and the import name
stays `nepdate` (ADR-0007). The options above are kept as history.

The import name stays `nepdate` either way. Installing both this and the old package would clash
on that import name; the old one has no users worth counting, so this is accepted.

## Sources

PyPI JSON API (`https://pypi.org/pypi/<name>/json`), https://pepy.tech, https://pypistats.org,
and the repositories: amitgaru/nepali-datetime, 4mritGiri/npdatetime, opensource-nepal/py-nepali,
ashok095/bikram-sambat, aerawatcorp/bikram, SushilShrestha/pyBSDate,
shivathapaa/nepali_calendar_utils, akakritagya/nepkit (all on GitHub).

# Other Python packages for the Bikram Sambat calendar

Checked 2026-11-02 against PyPI, pypistats, deps.dev and GitHub. The selection follows
[`shared/spec/BENCHMARK.md`](../shared/spec/BENCHMARK.md) section 7. Usage is pypistats' last-month
downloads, read on 2026-11-02. The bar is 1,000 downloads last month, first release at least 12
months before 2026-11-02, a release or commit in the last 36 months, a license, not archived or
deprecated, and a build on the current Python.

## Candidate table

| Package | Last month | First release | Last release | License | Verdict |
|---|---:|---|---|---|---|
| `nepali-datetime` | 25,086 | 2020-07-19 | 2026-05-07 | MIT | selected |
| `nepalicalendar` | 2,009 | 2016-05-13 | 2016-06-01 | unknown | fails the 36-month bar and has no clear license |
| `nepali` | 1,397 | 2018-10-08 | 2026-02-02 | MIT | selected |
| `nepali-date` | 882 | 2019-01-07 | 2020-05-09 | MIT | fails 1,000 last month and the 36-month bar |
| `bikram` | 820 | 2016-11-13 | 2025-10-17 | MIT | fails 1,000 last month |
| `bikram-sambat` | 807 | 2025-06-12 | 2026-04-27 | MIT | fails 1,000 last month |
| `npdatetime` | 769 | 2025-01-04 | 2026-10-26 | MIT | fails 1,000 last month |
| `nepali-calendar-utils` | 167 | 2025-01-24 | 2026-09-19 | MPL-2.0 | fails 1,000 last month |
| `nepkit` | 265 | 2026-08-11 | 2026-09-10 | MIT | fails 1,000 last month and the 12-month bar |
| `nepali-date-utils` | 161 | 2024-02-03 | 2024-02-10 | GPL-3.0 | fails 1,000 last month |
| `nepali-date-converter` | 212 | 2023-07-03 | 2023-07-03 | unknown | fails 1,000 last month and the 36-month bar |
| `adbs` | 19 | 2016-09-18 | 2016-09-18 | Apache-2.0 | fails 1,000 last month and the 36-month bar |
| `datetime-nepali` | not measured | 2024-06-04 | 2024-06-07 | MIT | fails the 36-month bar |

`nepali-datetime` and `nepali` are separate packages from the same organization; `nepali` is not a
fork or a copy of `nepali-datetime`. `npdatetime` is a Rust/PyO3 extension, not pure Python, but it
still fails the usage minimum.

## Calls measured

| Package | B1 BS to AD | B2 AD to BS |
|---|---|---|
| `nepali-datetime` | `nepali_datetime.date(y, m, d).to_datetime_date()` | `nepali_datetime.date.from_datetime_date(ad)` |
| `nepali` | `converter.nepali_to_english(y, m, d)` | `converter.english_to_nepali(y, m, d)` |

Both packages return a `datetime.date` or a `(year, month, day)` tuple, normalised to a tuple before
comparison.

## Correctness

`nepali-datetime` differs from `shared/data` in 6 New Year dates (BS 2088, 2089, 2090, 2092, 2096 and
2097) and in month lengths in 17 years. `nepali` differs in 4 New Year dates (2085, 2088, 2089 and
2090). The report lists every differing date in the 64 inputs. A fast wrong answer is listed, never
ranked first.

### Dates rejected or different

Each row is one of the 64 BENCHMARK dates where the package raised or returned a date other than the
committed table. `rejected` means the call raised. The last column is `yes` when the Bikram Sambat
year is 2087, 2088, 2089 or 2090.

| Package | Direction | Input | Theirs | Ours | 2087 to 2090 |
|---|---|---|---|---|---|
| `nepali-datetime` | BS to AD | 2088-01-04 | 2031-04-18 | 2031-04-19 | yes |
| `nepali-datetime` | BS to AD | 2089-06-10 | 2032-09-26 | 2032-09-27 | yes |
| `nepali-datetime` | AD to BS | 2031-04-19 | 2088-01-05 | 2088-01-04 | yes |
| `nepali-datetime` | AD to BS | 2032-09-27 | 2089-06-11 | 2089-06-10 | yes |
| `nepali` | BS to AD | 2086-07-23 | 2029-11-09 | 2029-11-08 | no |
| `nepali` | BS to AD | 2088-01-04 | 2031-04-17 | 2031-04-19 | yes |
| `nepali` | BS to AD | 2089-06-10 | 2032-09-26 | 2032-09-27 | yes |
| `nepali` | AD to BS | 1943-04-14 | rejected | 2000-01-01 | no |
| `nepali` | AD to BS | 2029-11-08 | 2086-07-22 | 2086-07-23 | no |
| `nepali` | AD to BS | 2031-04-19 | 2088-01-06 | 2088-01-04 | yes |
| `nepali` | AD to BS | 2032-09-27 | 2089-06-11 | 2089-06-10 | yes |

## Sources

PyPI JSON API (`https://pypi.org/pypi/<name>/json`), https://pypistats.org/api/packages/<name>/recent,
deps.dev, and the repositories: amitgaru/nepali-datetime and opensource-nepal/py-nepali.

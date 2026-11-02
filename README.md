<p align="center">
  <img src="https://raw.githubusercontent.com/sanamhub/nepdate-python/main/docs/assets/nepdate-python-128.png" width="128" alt="NepDate for Python logo">
</p>

<h1 align="center">nepdate-python</h1>

<p align="center">
  <a href="https://github.com/sanamhub/nepdate-python/actions/workflows/ci.yml"><img src="https://github.com/sanamhub/nepdate-python/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/nepdate-core/"><img src="https://img.shields.io/pypi/v/nepdate-core?include_prereleases&label=nepdate-core&logo=pypi&logoColor=white" alt="nepdate-core on PyPI"></a>
  <a href="https://pypi.org/project/nepdate-patro/"><img src="https://img.shields.io/pypi/v/nepdate-patro?include_prereleases&label=nepdate-patro&logo=pypi&logoColor=white" alt="nepdate-patro on PyPI"></a>
  <a href="https://pypi.org/project/nepdate-core/"><img src="https://img.shields.io/pypi/pyversions/nepdate-core?logo=python&logoColor=white" alt="Python versions"></a>
  <a href="https://github.com/sanamhub/nepdate-python/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License: MIT"></a>
</p>

Bikram Sambat (Nepali calendar) dates, conversion, formatting, parsing, ranges and fiscal
years for Python 3.11 and newer. Part of the NepDate family: the shared data and spec live in
the hub [`sanamhub/nepdate`](https://github.com/sanamhub/nepdate); the C# original is
[NepDate](https://github.com/RajuPrasai/NepDate).

> **Status:** 0.1.0-rc.1 (`0.1.0rc1` on PyPI), a release candidate. The API is listed in
> [docs/API.md](https://github.com/sanamhub/nepdate-python/blob/main/docs/API.md) and may still
> change before 0.1.0. Patro data (tithi, holidays, events) is informational, not an official
> calendar.

- Import `nepdate`. The core distribution is `nepdate-core`, because `nepdate` on PyPI belongs to
  an unrelated project (ADR-0007).
- Tithi, public holidays and events are a separate distribution, `nepdate-patro` (import
  `nepdate_patro`). The core has none of that data.
- Pure Python, zero runtime dependencies (except `tzdata` on Windows, for `today()`), typed
  (`py.typed`), and works on free-threaded 3.14t.
- BS 1901-01-01 to 2199-12-30 (AD 1844-04-11 to 2143-04-15). Same results as C# NepDate and the
  other ports, proved by the shared vectors.

## Install

```console
pip install --pre nepdate-core
```

`--pre` is needed while only pre-releases exist; pin `nepdate-core==0.1.0rc1` to stay on this one.

## Dates

```python
>>> from nepdate import MAX, MIN, Lang, NepaliDate
>>> d = NepaliDate(2080, 5, 15)
>>> str(d)
'2080/05/15'
>>> d.to_date()
datetime.date(2023, 9, 1)
>>> d.month_enum.label(), d.weekday.label()
('Bhadra', 'Friday')
>>> d.day_of_year, d.month_length, d.year_length
(141, 31, 365)
>>> d.last_of_month()
NepaliDate(2080, 5, 31)
>>> MIN.isoformat(), MAX.isoformat()
('1901-01-01', '2199-12-30')

```

A date is immutable, hashable and comparable, so it sorts and works as a dict key. Validation
runs year, then month, then day; a failing value raises `NepDateError`. `today(tz=None)` reads the
clock in Nepal time unless another `datetime.tzinfo` is given, and `is_today`,
`is_yesterday` and `is_tomorrow` take the same zone argument.

## Conversion and serialization

```python
>>> import datetime
>>> from nepdate import NepaliDate, to_english_dates, to_nepali_dates
>>> d = NepaliDate(2080, 5, 15)
>>> NepaliDate.from_date(datetime.date(2023, 9, 1)) == d
True
>>> d.isoformat()
'2080-05-15'
>>> d.to_json()
'"2080-05-15"'
>>> NepaliDate.from_json('"2080-05-15"') == d
True
>>> d.to_ymd_int()
20800515
>>> NepaliDate.from_ymd_int(20800515) == d
True
>>> d.to_ordinal()
738764
>>> NepaliDate.from_ordinal(738764) == d
True
>>> to_nepali_dates([datetime.date(2023, 9, 1)])
[NepaliDate(2080, 5, 15)]
>>> to_english_dates(["2080-05-15"])
[datetime.date(2023, 9, 1)]

```

The canonical text form is `YYYY-MM-DD`, and `to_json` returns that string already quoted, so it
can be written into a JSON document without another encoder. The batch functions keep the input
order. `pickle` and `copy` rebuild the same date.

## Arithmetic

```python
>>> from nepdate import NepaliDate, Overflow
>>> d = NepaliDate(2080, 5, 15)
>>> d.add_days(1000)
NepaliDate(2083, 2, 14)
>>> d.add_months(13)
NepaliDate(2081, 6, 15)
>>> d.add_months(-5)
NepaliDate(2079, 12, 15)
>>> d.add_years(1)
NepaliDate(2081, 5, 15)
>>> NepaliDate(2081, 4, 32).add_months(2)
NepaliDate(2081, 6, 30)
>>> NepaliDate(2081, 4, 32).add_months(2, Overflow.SPILL)
NepaliDate(2081, 7, 2)

```

A whole month moves in month space; the overflow mode chooses between clamping to the target
month end and spilling into the next month. A result outside the supported range raises
`NepDateError`.

The day difference has two names with opposite signs. `days_until(other)` is `other - self`, and
the `-` operator keeps the C# direction, `self - other`, as a `datetime.timedelta`:

```python
>>> from nepdate import NepaliDate
>>> a, b = NepaliDate(2080, 5, 15), NepaliDate(2080, 5, 20)
>>> a.days_until(b)
5
>>> b - a
datetime.timedelta(days=5)
>>> a.diff(b)
DateDiff(negative=False, years=0, months=0, days=5, total_days=5)

```

## Formatting

```python
>>> from nepdate import DateOrder, Lang, NepaliDate, Separator
>>> d = NepaliDate(2080, 5, 15)
>>> d.short(DateOrder.DMY, Separator.DASH, pad=False)
'15-5-2080'
>>> d.short(lang=Lang.NE)
'२०८०/०५/१५'
>>> d.long(weekday=True)
'Friday, Bhadra 15, 2080'
>>> d.long(weekday=True, lang=Lang.NE)
'शुक्रवार, भदौ १५, २०८०'
>>> d.format("dd MMMM yyyy")
'15 Bhadra 2080'
>>> d.format("MMM")
'Bha'
>>> f"{d:yyyy-MM-dd}"
'2080-05-15'

```

`short` takes the field order, separator, padding and language. `long` writes
`[Weekday, ]Month day[, year]`. `format` runs the hub's pattern language, and the `YYYYMMDD`
integer form is covered under conversion.

## Parsing

```python
>>> from nepdate import NepaliDate
>>> NepaliDate.parse("2080/05/15")
NepaliDate(2080, 5, 15)
>>> NepaliDate.parse("२०८०।०५।१५")
NepaliDate(2080, 5, 15)
>>> NepaliDate.parse_lenient("15 Bhadra 2080")
NepaliDate(2080, 5, 15)
>>> NepaliDate.try_parse("not a date") is None
True
>>> NepaliDate.try_parse_lenient("15 Bhadra 2080")
NepaliDate(2080, 5, 15)

```

`parse` is the strict form, year then month then day, with ASCII or Devanagari digits and the
eight separators of the hub's `PARSING.md`. `parse_lenient` accepts month names, era markers and
the two numeric orders, and never guesses a two-digit year. The `try_` forms return `None`
instead of raising.

## Ranges

```python
>>> from nepdate import DateRange, NepaliDate
>>> r = DateRange.month(2080, 5)
>>> r.start, r.end
(NepaliDate(2080, 5, 1), NepaliDate(2080, 5, 31))
>>> len(r), NepaliDate(2080, 5, 15) in r
(31, True)
>>> r.contains_range(DateRange.single(NepaliDate(2080, 5, 15)))
True
>>> a = DateRange(NepaliDate(2080, 5, 10), NepaliDate(2080, 5, 20))
>>> a.intersect(DateRange(NepaliDate(2080, 5, 15), NepaliDate(2080, 5, 25)))
DateRange(NepaliDate(2080, 5, 15), NepaliDate(2080, 5, 20))
>>> [str(piece) for piece in a.split_by_month()]
['2080/05/10 - 2080/05/20']
>>> [str(piece) for piece in a.difference(DateRange.single(NepaliDate(2080, 5, 15)))]
['2080/05/10 - 2080/05/14', '2080/05/16 - 2080/05/20']

```

A range is inclusive and never empty: a start after the end is refused. `len` is the day count,
iteration yields every day in order, and the set operations are `contains_range`, `overlaps`,
`is_adjacent_to`, `intersect`, `union` and `difference`. `split_by_month`,
`split_by_fiscal_quarter`, `dates_with_interval`, `working_days` and `weekend_days` return every
piece or date up to the last supported day instead of failing at it. `str(range)` is
`"start - end"`, and `to_string(order, sep, lang)` formats both ends.

## Fiscal year

```python
>>> from nepdate import FiscalYear, NepaliDate, Quarter
>>> fy = FiscalYear.containing(NepaliDate(2080, 5, 15))
>>> fy.label()
'2080/81'
>>> fy.start(), fy.end()
(NepaliDate(2080, 4, 1), NepaliDate(2081, 3, 31))
>>> fy.range()
DateRange(NepaliDate(2080, 4, 1), NepaliDate(2081, 3, 31))
>>> fy.quarter_range(Quarter.Q2)
DateRange(NepaliDate(2080, 7, 1), NepaliDate(2080, 9, 29))

```

A fiscal year starts on 1 Shrawan and ends on the last day of Ashad of the following BS year.
`FiscalYear(2080)` names it by its start year, `containing(date)` finds it from a date, and
`quarter_range(q)` gives one of the four quarters. `NepaliDate.fiscal_year()` and
`NepaliDate.quarter()` are the date's own shortcuts.

## Errors

```python
>>> from nepdate import ErrorKind, NepDateError, NepaliDate
>>> try:
...     NepaliDate(2080, 1, 40)
... except NepDateError as error:
...     error.kind is ErrorKind.INVALID_DAY
True
>>> NepaliDate.try_parse("2080/13/01") is None
True

```

Every failure raises `NepDateError`, a `ValueError` subclass, whose `kind` is an `ErrorKind`.
The parse kinds are `INVALID_CHARACTER`, `WRONG_GROUP_COUNT`, `NUMBER_TOO_LONG`, `AMBIGUOUS` and
`UNRECOGNIZED`; validation adds `OUT_OF_RANGE`, `INVALID_MONTH`, `INVALID_DAY` and
`INVALID_GREGORIAN`.

## Patro: tithi, holidays and events

The core has no patro data. Install both distributions:

```console
pip install --pre nepdate-core nepdate-patro
```

```python
>>> from nepdate import Lang, NepaliDate
>>> from nepdate_patro import coverage, info
>>> day = info(NepaliDate(2080, 5, 15))
>>> day.is_public_holiday
True
>>> day.tithi.label(Lang.EN)
'Dwitiya'
>>> [event.label(Lang.EN) for event in day.events]
['Saparu (Gaijatra) (Kathmandu Holiday)', 'Ropain Jatra']
>>> coverage().start
NepaliDate(2077, 1, 1)

```

`info` never raises: a date outside the coverage returns one shared empty `CalendarInfo`. The
data currently covers BS 2077-01-01 to 2084-08-20.

## API

The complete signatures, defaults, exceptions and an example per group are in the
[API reference](https://github.com/sanamhub/nepdate-python/blob/main/docs/API.md).

| Module | Exported names |
|---|---|
| `nepdate` | `MIN`, `MAX`, `NepaliDate`, `Lang`, `Month`, `Weekday`, `Overflow`, `DateOrder`, `Separator`, `DateDiff`, `FiscalYear`, `Quarter`, `DateRange`, `ErrorKind`, `NepDateError`, `to_nepali_digits`, `to_nepali_dates`, `to_english_dates` |
| `nepdate_patro` | `Tithi`, `Event`, `CalendarInfo`, `info`, `coverage`, `public_holidays` |

## Documentation

| Page | What it covers |
|---|---|
| [Guides](https://nepdate.com/docs/python/) | Install, usage and examples on nepdate.com |
| [API](https://github.com/sanamhub/nepdate-python/blob/main/docs/API.md) | The complete public surface, group by group |
| [Benchmarks](https://github.com/sanamhub/nepdate-python/blob/main/docs/benchmarks.md) | B1 to B8 against the other Python packages and C# NepDate |
| [Competitors](https://github.com/sanamhub/nepdate-python/blob/main/docs/competitors.md) | The Python packages in the benchmark |
| [Mutation testing](https://github.com/sanamhub/nepdate-python/blob/main/docs/mutation.md) | How the test suite is checked against mutmut |
| [Fuzzing](https://github.com/sanamhub/nepdate-python/blob/main/docs/fuzzing.md) | How the parsers and formatter are fuzzed with atheris |
| [Release](https://github.com/sanamhub/nepdate-python/blob/main/docs/release.md) | The pre-tag matrix, freshness rule, rehearsal and post-publish check |
| [ADRs](https://github.com/sanamhub/nepdate-python/blob/main/docs/adr/README.md) | Why the design is what it is |
| [Changelog](https://github.com/sanamhub/nepdate-python/blob/main/CHANGELOG.md) | What changed in each version |
| [Contributing](https://github.com/sanamhub/nepdate-python/blob/main/CONTRIBUTING.md) | Setup, tests and commits |
| [Security](https://github.com/sanamhub/nepdate-python/blob/main/SECURITY.md) | Reporting a vulnerability |
| [Data error form](https://github.com/sanamhub/nepdate/issues/new/choose) | A wrong date, holiday or tithi, reported in the hub |
| [Spec](https://github.com/sanamhub/nepdate/tree/main/spec) | Behaviour and vectors, in the hub |
| [Other languages](https://github.com/sanamhub/nepdate#packages) | The same library for Rust, Go, TypeScript, Swift, Kotlin and C++ |

## License

MIT ([LICENSE](https://github.com/sanamhub/nepdate-python/blob/main/LICENSE)). Calendar data from
NepDate by Raju Prasai and contributors, MIT
([NOTICE](https://github.com/sanamhub/nepdate-python/blob/main/shared/data/NOTICE)). Not affiliated
with the Government of Nepal.

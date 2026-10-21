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

Bikram Sambat (Nepali calendar) dates, conversion, formatting and parsing for Python 3.11 and
newer. Part of the NepDate family: the shared data and spec live in the hub
[`sanamhub/nepdate`](https://github.com/sanamhub/nepdate); the C# original is
[NepDate](https://github.com/RajuPrasai/NepDate).

> **Status:** 0.1.0-beta.1 (`0.1.0b1` on PyPI), the first public pre-release. The API is listed in
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

`--pre` is needed while only pre-releases exist; pin `nepdate-core==0.1.0b1` to stay on this one.

## Quick start

```python
>>> from nepdate import Lang, NepaliDate
>>> d = NepaliDate(2080, 5, 15)
>>> str(d)
'2080/05/15'
>>> d.to_date()
datetime.date(2023, 9, 1)
>>> d.long(weekday=True, lang=Lang.NE)
'शुक्रवार, भदौ १५, २०८०'
>>> NepaliDate.parse("2080/05/15") == d
True

```

Arithmetic stays on the BS calendar, so month lengths come from the shared data rather than from
the Gregorian calendar:

```python
>>> d.add_days(1000)
NepaliDate(2083, 2, 14)
>>> d.add_months(13)
NepaliDate(2081, 6, 15)
>>> d.fiscal_year().label()
'2080/81'

```

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

The complete signatures, defaults and exceptions are in the
[API contract](https://github.com/sanamhub/nepdate-python/blob/main/docs/API.md).

| Module | Exported names |
|---|---|
| `nepdate` | `MIN`, `MAX`, `NepaliDate`, `Lang`, `Month`, `Weekday`, `Overflow`, `DateOrder`, `Separator`, `DateDiff`, `FiscalYear`, `Quarter`, `DateRange`, `ErrorKind`, `NepDateError`, `to_nepali_digits` |
| `nepdate_patro` | `Tithi`, `Event`, `CalendarInfo`, `info`, `coverage`, `public_holidays` |

## Documentation

| Page | What it covers |
|---|---|
| [API](https://github.com/sanamhub/nepdate-python/blob/main/docs/API.md) | The complete public surface |
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

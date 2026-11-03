# Changelog

All notable changes to `nepdate-core` (import `nepdate`) and `nepdate-patro` are documented here.
The two distributions share this file and a version number (ADR-0005). The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0-rc.1] - 2026-11-03

### Added

- `NepaliDate.year_length`, the number of days in the BS year of a date, 364 through 367. It is
  the sum of the twelve BS month lengths and replaces the Gregorian `IsLeapYear` (D-12).
- `NepaliDate.is_today`, `is_yesterday` and `is_tomorrow`, each taking the zone to read the
  clock in; `None` means Nepal time, as in `today`.
- `NepaliDate.fromisoformat`, the strict parser under the name a `datetime.date` user expects
  next to `isoformat`.
- `NepaliDate.try_parse` and `try_parse_lenient`, the non-throwing forms of `parse` and
  `parse_lenient`; they return `None` instead of raising.
- `NepaliDate.from_ymd_int` and `to_ymd_int`, the `YYYYMMDD` integer form of a date.
- `NepaliDate.to_json`, `NepaliDate.from_json` and `__reduce__`, the native JSON and pickle
  hooks; `to_json` returns the quoted `YYYY-MM-DD` string.
- `to_nepali_dates` and `to_english_dates`, ordered batch conversion in both directions over any
  iterable.
- `DateRange.single`, `DateRange.from_day_count`, `DateRange.current_month`,
  `DateRange.current_fiscal_year` and `DateRange.current_calendar_year`.
- `DateRange.contains_range`, `overlaps`, `is_adjacent_to`, `intersect`, `union` and
  `difference`.
- `DateRange.split_by_month`, `split_by_fiscal_quarter`, `dates_with_interval`,
  `working_days` and `weekend_days`.
- `DateRange.to_string`, `DateRange.__eq__`, `DateRange.__hash__` and `DateRange.__repr__`.
- A grouped API reference with an example per group in `docs/API.md`, the same grouping and
  examples in the README, and a matching Python page on nepdate.com.

### Changed

- A format pattern that ends in a backslash now writes one backslash, as the formatting spec
  says, instead of dropping it.
- `docs/API.md` is grouped like the hub's `spec/API.md`, and every public item has a runnable
  example.
- The tests load every new shared vector: `year-length.tsv`, `day-diff.tsv`, `ymd-int.tsv`,
  `bulk.tsv`, `serialization.tsv`, `format-matrix.tsv`, `ranges.tsv`, `range-factories.tsv`,
  `range-splits.tsv`, `range-days.tsv` and `range-format.tsv`.
- The skipped catalogue rows for the range operations, the non-throwing parsers, range equality
  and range string forms now run with their assertions. The rows that stay skipped are the
  C# constructs that the hub decisions remove: the auto-adjust parser, `IComparable.CompareTo`,
  fractional arithmetic, `IsLeapYear`, null references and the default date.

### Breaking changes

- Two ranges with the same bounds now compare and hash equal. Before, a range used object
  identity, so two equal ranges were unequal and could be separate dictionary keys. Migration:
  compare the bounds directly, or use `is` where object identity matters.
- A format pattern that ends in a backslash now writes one backslash. Migration: remove the
  final backslash, or quote the character, when the old output did not include it.

## [0.1.0-rc.1] - 2026-11-03

### Changed

- The published-package check also runs weekly on Linux with pip, uv and poetry, and daily for
  PyPI metadata, and reports a failure through one `published-check` issue.

## [0.1.0-beta.1] - 2026-10-22

First public pre-release. The API may still change before 0.1.0. On PyPI the version is `0.1.0b1`;
install it with `pip install --pre nepdate-core nepdate-patro`.

### Added

- `NepaliDate` with construction, accessors, BS to AD and AD to BS conversion, ordinals,
  comparisons and `MIN`/`MAX`.
- The `Lang`, `Month`, `Weekday` and `ErrorKind` enums and the `NepDateError` exception.
- Day, month and year arithmetic (`add_days`, `add_months`, `add_years`, `days_until`,
  `diff` and the timedelta operators), the `Overflow`, `Quarter`, `DateDiff` and
  `FiscalYear` types, and `DateRange`.
- Formatting: `str`, `repr`, `isoformat`, `short`, `long`, `format` and `__format__`, the
  `DateOrder` and `Separator` enums, the month and weekday labels, and `to_nepali_digits`.
- Parsing: `NepaliDate.parse` for the strict form and `NepaliDate.parse_lenient` for
  human-written dates with month names, era markers or Devanagari digits.
- `NepaliDate.today(tz=None)`, which reads the clock in Nepal time by default.
- The `nepdate-patro` distribution (BS 2077 to 2084): `Tithi`, `Event` and `CalendarInfo`,
  `info` for one day, `coverage` for the data range, and `public_holidays` for the
  gazetted dates.
- The core distribution is `nepdate-core` on PyPI, because `nepdate` there belongs to an
  unrelated project; the import name is `nepdate` (ADR-0007).


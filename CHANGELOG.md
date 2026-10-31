# Changelog

All notable changes to `nepdate-core` (import `nepdate`) and `nepdate-patro` are documented here.
The two distributions share this file and a version number (ADR-0005). The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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


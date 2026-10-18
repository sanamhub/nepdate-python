# Changelog

All notable changes to `nepdate` and `nepdate-patro` are documented here. The two distributions
share this file and a version number (ADR-0005). The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-10-18

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
  `info` for one day, `coverage` for the data range, and `public_holidays` for the 294
  gazetted dates.

### Changed

- The core distribution is published as `nepdate-core`; the import name is still `nepdate` and
  `nepdate-patro` now depends on `nepdate-core` (ADR-0007).


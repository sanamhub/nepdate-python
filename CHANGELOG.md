# Changelog

All notable changes to `nepdate` and `nepdate-patro` are documented here. The two distributions
share this file and a version number (ADR-0005). The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `NepaliDate` with construction, accessors, BS to AD and AD to BS conversion, ordinals,
  comparisons and `MIN`/`MAX`.
- The `Lang`, `Month`, `Weekday` and `ErrorKind` enums and the `NepDateError` exception.
- Day, month and year arithmetic (`add_days`, `add_months`, `add_years`, `days_until`,
  `diff` and the timedelta operators), the `Overflow`, `Quarter`, `DateDiff` and
  `FiscalYear` types, and `DateRange`.

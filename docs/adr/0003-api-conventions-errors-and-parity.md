# ADR-0003: API conventions, errors and parity mapping

- Status: Accepted
- Date: 2026-09-25 (amended 2026-10-07 for hub ADR-0004)
- Deciders: Sanam Pakuwal

## Decision

**Conventions** (full surface in `docs/API.md`):
- Behave like `datetime.date` where the meaning is the same: `NepaliDate(y, m, d)` raises on invalid
  input, objects are immutable and hashable, `__str__`/`__repr__`/`__format__`, `+`/`-` with
  `timedelta`, ordinals shared with `datetime.date`.
- **Don't subclass `datetime.date`**: its fields are AD, so inherited `replace()`, `isoformat()` and
  `strftime()` would silently mix calendars.
- Arguments are validated with `operator.index`, so `NepaliDate(True, 1, 1)` and floats raise
  `TypeError` (`bool` is an `int` subclass).
- `today(tz=None)` means Nepal time (`ZoneInfo("Asia/Kathmandu")`), not the host's zone. `from_date`
  given an aware `datetime` uses that datetime's own `.date()`; the docstring tells callers to
  convert to Nepal time first when they mean "the date in Nepal".
- Weekday numbering follows the spec (Sunday = 0); the docstring warns that `date.weekday()` is
  Monday = 0.
- Comparisons with other types return `NotImplemented`.

**Errors:** one exception type, `NepDateError(ValueError)`, with a `kind: ErrorKind`. Subclassing
`ValueError` keeps `except ValueError` working, as with `datetime.date`.

**Parity** (`shared/spec/PARITY.md`, applies unchanged):

| ID | Python |
|---|---|
| D-01 | no default constructor; `NepaliDate()` is a `TypeError` |
| D-02, D-03 | `add_months(n, Overflow)`, `add_days(n)`, integers only; `timedelta` with a non-whole day raises |
| D-04 | `Month.short_label()` returns `Asa` / `Aso` |
| D-05, D-06 | `parse` (strict), `parse_lenient` |
| D-07 | `days_until() -> int` |
| D-08 | `FiscalYear` with `start`, `end`, `quarter_range` |
| D-09 | `DateRange`: `len`, `in`, iteration only |
| D-10 | not ported |
| D-11 | `isoformat()` is `"YYYY-MM-DD"` |
| D-12 | `month_length`; year length via `len(DateRange.year(y))` |
| D-13 | separate distribution `nepdate-patro`, import `nepdate_patro` (ADR-0001 §1) |
| D-14 | not ported; `today()` and `add_days(±1)` |
| D-15 | `lang` parameter on every formatter |

A Python-only deviation is not allowed; propose it to the hub.

# `nepdate` and `nepdate_patro` (Python): API reference (v0.1)

The complete public surface (`__all__` of each package) for v0.1, grouped like the hub's
`spec/API.md`. A new public name needs this file changed in the same pull request, approved by
the maintainer. Behaviour is specified in the hub's `spec/` directory; naming and error
conventions are in ADR-0003. Every value type here is immutable and hashable, and uses
`__slots__`. The distributions are `nepdate-core` (import `nepdate`) and `nepdate-patro` (import
`nepdate_patro`).

The examples assume `import datetime` and `from nepdate import ...`; each block imports what it
uses, so it can be pasted into a session on its own. Python 3.11 or newer.

## Module constants

The supported range is 1901-01-01 through 2199-12-30 BS, which is 1844-04-11 through
2143-04-15 AD.

```text
MIN: NepaliDate  # 1901-01-01
MAX: NepaliDate  # 2199-12-30
```

```python
>>> from nepdate import MAX, MIN
>>> MIN.isoformat(), MAX.isoformat()
('1901-01-01', '2199-12-30')
>>> MAX.to_date()
datetime.date(2143, 4, 15)

```

## 1. Dates, identity and comparison

A `NepaliDate` is a Bikram Sambat date. The constructor validates the year, then the month, then
the day, and raises `NepDateError` with the failing `ErrorKind`. There is no default or empty
date: a value that exists is valid (D-01). Comparisons use chronological order and every
comparison with another type returns `NotImplemented`, so `==` is `False` and `<` raises
`TypeError`, as with `datetime.date`.

```text
class NepaliDate:
    def __init__(self, year: int, month: int, day: int) -> None: ...

    @classmethod
    def from_date(cls, d: datetime.date) -> NepaliDate: ...
    @classmethod
    def from_ordinal(cls, n: int) -> NepaliDate: ...
    @classmethod
    def today(cls, tz: datetime.tzinfo | None = None) -> NepaliDate: ...

    @classmethod
    def parse(cls, s: str) -> NepaliDate: ...
    @classmethod
    def parse_lenient(cls, s: str) -> NepaliDate: ...
    @classmethod
    def try_parse(cls, s: str) -> NepaliDate | None: ...
    @classmethod
    def try_parse_lenient(cls, s: str) -> NepaliDate | None: ...

    year: int
    month: int
    day: int
    month_enum: Month
    weekday: Weekday
    day_of_year: int
    month_length: int
    year_length: int

    def first_of_month(self) -> NepaliDate: ...
    def last_of_month(self) -> NepaliDate: ...
    def to_date(self) -> datetime.date: ...
    def to_ordinal(self) -> int: ...

    def is_today(self, tz: datetime.tzinfo | None = None) -> bool: ...
    def is_yesterday(self, tz: datetime.tzinfo | None = None) -> bool: ...
    def is_tomorrow(self, tz: datetime.tzinfo | None = None) -> bool: ...
```

`weekday` numbers Sunday as 0, the spec's numbering, unlike `datetime.date.weekday()`, which
numbers Monday as 0. `day_of_year` counts from Baishakh 1 of the BS year. `year_length` is the
sum of the twelve BS month lengths, 364 through 367; it replaces the Gregorian `IsLeapYear` of
C# (D-12). `today`, `is_today`, `is_yesterday` and `is_tomorrow` read the clock in `tz`, and
`None` means Nepal time (`Asia/Kathmandu`), not the host's zone.

```python
>>> import datetime
>>> from nepdate import NepaliDate, Weekday
>>> d = NepaliDate(2081, 4, 15)
>>> d.year, d.month, d.day
(2081, 4, 15)
>>> d.month_enum.label()
'Shrawan'
>>> d.weekday is Weekday.TUESDAY
True
>>> d.day_of_year
109
>>> d.month_length, d.year_length
(32, 366)
>>> d.last_of_month()
NepaliDate(2081, 4, 32)
>>> d.to_date()
datetime.date(2024, 7, 30)
>>> NepaliDate.from_date(datetime.date(2024, 7, 30)) == d
True

```

### Ordered comparisons and hashing

`NepaliDate` supports `==`, `!=`, `<`, `<=`, `>`, `>=` and `hash`, in chronological order.
Dates in a sorted list are in calendar order, and equal dates hash equal, so a date can be a
dict key or a set member.

```python
>>> from nepdate import NepaliDate
>>> sorted([NepaliDate(2081, 5, 1), NepaliDate(2081, 4, 32), NepaliDate(2081, 4, 1)])
[NepaliDate(2081, 4, 1), NepaliDate(2081, 4, 32), NepaliDate(2081, 5, 1)]
>>> NepaliDate(2081, 4, 15) in {NepaliDate(2081, 4, 15)}
True

```

## 2. Conversion and serialization

The canonical text form is `YYYY-MM-DD`. `isoformat()` and `fromisoformat()` are the pair a
`datetime.date` user expects, and `from_date()` / `to_date()` are the Gregorian pair. The
`YYYYMMDD` integer form is kept from the C# `TypeConverter`, alongside the canonical text form (D-11). `to_json()` and
`from_json()` are the native JSON hook: the value is already the JSON string, so a caller can
write it into a document without another encoder. `__reduce__` makes `pickle` and `copy` work.
The serialization object form, the XML serializer and the converter type are not ported (D-11).

```text
class NepaliDate:
    def isoformat(self) -> str: ...
    @classmethod
    def fromisoformat(cls, s: str) -> NepaliDate: ...
    @classmethod
    def from_json(cls, text: str) -> NepaliDate: ...
    def to_json(self) -> str: ...
    @classmethod
    def from_ymd_int(cls, n: int) -> NepaliDate: ...
    def to_ymd_int(self) -> int: ...
```

```python
>>> from nepdate import NepaliDate
>>> d = NepaliDate(2081, 4, 15)
>>> d.isoformat()
'2081-04-15'
>>> NepaliDate.fromisoformat(d.isoformat()) == d
True
>>> d.to_ymd_int()
20810415
>>> NepaliDate.from_ymd_int(20810415) == d
True
>>> d.to_json()
'"2081-04-15"'
>>> NepaliDate.from_json('"2081-04-15"') == d
True

```

`from_json` refuses a JSON `null` and any value that is not a quoted date string, because there
is no default date to put in its place (D-01).

### Batch conversion

One ordered function each way, taking any iterable: an AD `datetime.date` sequence into BS, and
a BS `NepaliDate` or strict date string sequence into AD. The output keeps the input order,
which is what a port promises even where the C# parallel path does not.

```text
def to_nepali_dates(dates: Iterable[datetime.date]) -> list[NepaliDate]: ...
def to_english_dates(items: Iterable[NepaliDate | str]) -> list[datetime.date]: ...
```

```python
>>> import datetime
>>> from nepdate import NepaliDate, to_english_dates, to_nepali_dates
>>> to_nepali_dates([datetime.date(2024, 7, 31), datetime.date(2000, 1, 1)])
[NepaliDate(2081, 4, 16), NepaliDate(2056, 9, 17)]
>>> to_english_dates(["2081-04-15", NepaliDate(2081, 4, 16)])
[datetime.date(2024, 7, 30), datetime.date(2024, 7, 31)]

```

A bad string stops the batch and raises `NepDateError`; nothing past it is converted.

## 3. Arithmetic

Day arithmetic moves by Gregorian ordinal; month and year arithmetic stays on the BS calendar
and reads the shared month-length table. `add_months` and `add_years` take an integer and an
explicit `Overflow`: `CLAMP` caps the day at the target month's length, `SPILL` carries the
excess into the following month (D-02, D-03). A negative count is the subtraction path. The
result outside 1901-01-01 through 2199-12-30 raises `NepDateError`.

```text
class NepaliDate:
    def add_days(self, n: int) -> NepaliDate: ...
    def add_months(self, n: int, overflow: Overflow = Overflow.CLAMP) -> NepaliDate: ...
    def add_years(self, n: int, overflow: Overflow = Overflow.CLAMP) -> NepaliDate: ...
    def days_until(self, other: NepaliDate) -> int: ...
    def diff(self, other: NepaliDate) -> DateDiff: ...

class Overflow(enum.Enum):
    CLAMP = "clamp"
    SPILL = "spill"
```

```python
>>> from nepdate import NepaliDate, Overflow
>>> d = NepaliDate(2081, 4, 30)
>>> d.add_days(3)
NepaliDate(2081, 5, 1)
>>> d.add_months(2)
NepaliDate(2081, 6, 30)
>>> d.add_months(2, Overflow.SPILL)
NepaliDate(2081, 6, 30)
>>> NepaliDate(2081, 4, 15).add_years(1)
NepaliDate(2082, 4, 15)
>>> NepaliDate(2081, 4, 15).days_until(NepaliDate(2081, 4, 16))
1

```

### Day difference and the `datetime.timedelta` operators

`days_until(other)` is the signed count `other - self`, the direction of the hub's
`days_between(a, b)` (D-07). `d - other` returns a `datetime.timedelta` in the C# direction,
`self - other`, positive when `self` is later. The two directions answer different questions and
are not interchangeable. `d + timedelta` and `d - timedelta` accept whole days only.

`diff(other)` returns a `DateDiff` with `negative`, `years`, `months`, `days` and `total_days`.

```text
class DateDiff:
    negative: bool
    years: int
    months: int
    days: int
    total_days: int
```

```python
>>> import datetime
>>> from nepdate import NepaliDate
>>> a, b = NepaliDate(2081, 4, 15), NepaliDate(2081, 4, 16)
>>> a.days_until(b), b.days_until(a)
(1, -1)
>>> a - b, b - a
(datetime.timedelta(days=-1), datetime.timedelta(days=1))
>>> a + datetime.timedelta(days=10)
NepaliDate(2081, 4, 25)
>>> a.diff(NepaliDate(2082, 4, 15))
DateDiff(negative=False, years=1, months=0, days=0, total_days=366)

```

## 4. Formatting

`str` is the default display `YYYY/MM/DD`. `short` writes the three fields in a chosen order
(`DateOrder`), with a chosen separator (`Separator`), with or without padding, and in English or
Nepali digits (`Lang`). `long` writes `[Weekday, ]Month day[, year]`. `format` runs the custom
pattern language, and `f"{d:...}"` is the same with English. Weekday and month names come from
`Weekday` and `Month`, whose `label` and `short_label` take a `Lang`.

```text
class NepaliDate:
    def short(
        self,
        order: DateOrder = DateOrder.YMD,
        sep: Separator = Separator.SLASH,
        pad: bool = True,
        lang: Lang = Lang.EN
    ) -> str: ...
    def long(
        self,
        *,
        weekday: bool = False,
        year: bool = True,
        pad: bool = True,
        lang: Lang = Lang.EN
    ) -> str: ...
    def format(self, pattern: str, lang: Lang = Lang.EN) -> str: ...
```

```text
class Lang(enum.Enum):
    EN = "en"
    NE = "ne"

class Month(enum.IntEnum):
    BAISHAKH = 1
    JESTHA = 2
    ASHAD = 3
    SHRAWAN = 4
    BHADRA = 5
    ASHOJ = 6
    KARTIK = 7
    MANGSIR = 8
    POUSH = 9
    MAGH = 10
    FALGUN = 11
    CHAITRA = 12

    def label(self, lang: Lang = Lang.EN) -> str: ...
    def short_label(self, lang: Lang = Lang.EN) -> str: ...

class Weekday(enum.IntEnum):
    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6

    def label(self, lang: Lang = Lang.EN) -> str: ...
    def short_label(self, lang: Lang = Lang.EN) -> str: ...

class DateOrder(enum.Enum):
    YMD = "YMD"
    YDM = "YDM"
    MYD = "MYD"
    MDY = "MDY"
    DYM = "DYM"
    DMY = "DMY"

class Separator(enum.Enum):
    SLASH = "/"
    BACKSLASH = "\\"
    DOT = "."
    UNDERSCORE = "_"
    DASH = "-"
    SPACE = " "
```

The month short names are `Bai`, `Jes`, `Asa`, `Shr`, `Bha`, `Aso`, `Kar`, `Man`, `Pou`, `Mag`,
`Fal` and `Cha`; `Asa` and `Aso` fix the C# `Ash` collision for Ashad and Ashoj (D-04). Nepali
has no customary abbreviation, so `short_label` returns the full name for `Lang.NE`.

The pattern tokens are `yyyy` and longer runs for the four-digit year, `y`, `yy` and `yyy` for
the last two digits, `MMMM` for the full month name, `MMM` for the short name, `MM` and `M` for
the month, `dd` for a padded day and any other `d` run for an unpadded day. A backslash escapes
the next character, a trailing backslash writes one backslash, and text in single quotes is
literal. `""`, `G`, `g` and `d` are the default display, `D` is the long form and `s` is
`YYYY-MM-DD`.

```python
>>> from nepdate import DateOrder, Lang, NepaliDate, Separator
>>> d = NepaliDate(2081, 4, 15)
>>> str(d)
'2081/04/15'
>>> d.short(DateOrder.DMY, Separator.DASH, pad=False)
'15-4-2081'
>>> d.short(lang=Lang.NE)
'२०८१/०४/१५'
>>> d.long(weekday=True)
'Tuesday, Shrawan 15, 2081'
>>> d.long(weekday=True, lang=Lang.NE)
'मङ्गलवार, साउन १५, २०८१'
>>> d.format("dd MMMM yyyy")
'15 Shrawan 2081'
>>> d.format("MMM yyyy")
'Shr 2081'
>>> f"{d:yyyy-MM-dd}"
'2081-04-15'

```

`to_nepali_digits(n, min_width=0)` formats an integer with Devanagari digits and optional zero
padding, for building output around a date.

```text
def to_nepali_digits(n: int, min_width: int = 0) -> str: ...
```

```python
>>> from nepdate import to_nepali_digits
>>> to_nepali_digits(2081), to_nepali_digits(81, 2)
('२०८१', '८१')

```

## 5. Parsing

`parse` is the strict parser: exactly year, month and day in that order. The separators are
`-`, `/`, `.`, `_`, `\`, space, `|` and `।`. Devanagari digits are accepted and may be mixed
with ASCII; a group is capped at four digits (D-05). Leading, trailing and repeated separators
are ignored. `fromisoformat` is the same parser under the name a `datetime.date` user expects.
`parse_lenient` first tries the strict form, then applies the closed month-name
list, era markers and the numeric orders of the hub's `PARSING.md` section 2; a two-digit year is
never expanded (D-06). `try_parse` and `try_parse_lenient` are the non-throwing forms and return
`None` instead of raising.

```text
class NepaliDate:
    @classmethod
    def parse(cls, s: str) -> NepaliDate: ...
    @classmethod
    def parse_lenient(cls, s: str) -> NepaliDate: ...
    @classmethod
    def try_parse(cls, s: str) -> NepaliDate | None: ...
    @classmethod
    def try_parse_lenient(cls, s: str) -> NepaliDate | None: ...
```

```python
>>> from nepdate import NepaliDate
>>> NepaliDate.parse("2081/04/15")
NepaliDate(2081, 4, 15)
>>> NepaliDate.parse("२०८१।०४।१५")
NepaliDate(2081, 4, 15)
>>> NepaliDate.parse_lenient("15 Shrawan 2081")
NepaliDate(2081, 4, 15)
>>> NepaliDate.try_parse("not a date") is None
True
>>> NepaliDate.try_parse_lenient("15 Shrawan 2081")
NepaliDate(2081, 4, 15)

```

### Errors

Every failure raises `NepDateError`, a `ValueError` subclass, whose `kind` names the failed
rule. The parse kinds are `INVALID_CHARACTER`, `WRONG_GROUP_COUNT`, `NUMBER_TOO_LONG`,
`AMBIGUOUS` and `UNRECOGNIZED`; validation adds `OUT_OF_RANGE`, `INVALID_MONTH`, `INVALID_DAY`
and `INVALID_GREGORIAN`. `except ValueError` keeps working for code written against
`datetime.date`.

```text
class ErrorKind(enum.Enum):
    OUT_OF_RANGE = "out_of_range"
    INVALID_MONTH = "invalid_month"
    INVALID_DAY = "invalid_day"
    INVALID_GREGORIAN = "invalid_gregorian"
    INVALID_CHARACTER = "invalid_character"
    WRONG_GROUP_COUNT = "wrong_group_count"
    NUMBER_TOO_LONG = "number_too_long"
    AMBIGUOUS = "ambiguous"
    UNRECOGNIZED = "unrecognized"

class NepDateError(ValueError):
    def __init__(self, kind: ErrorKind, message: str) -> None: ...
    kind: ErrorKind
```

```python
>>> from nepdate import ErrorKind, NepDateError, NepaliDate
>>> try:
...     NepaliDate(2080, 13, 1)
... except NepDateError as error:
...     error.kind is ErrorKind.INVALID_MONTH
True

```

## 6. Ranges

`DateRange` is an inclusive span of two valid dates. A start after the end is refused, so a
range is never empty (D-01). `len(range)` is the number of days, `date in range` is containment,
and iterating yields every day in order. The set operations are value operations: `intersect`
returns a range or `None`, `union` is the smallest covering range, and `difference` returns
zero, one or two ranges. The splits clip the first and last piece to the range ends, and every
day helper includes the last supported day instead of failing at it (D-16).

```text
class DateRange:
    def __init__(self, start: NepaliDate, end: NepaliDate) -> None: ...

    @classmethod
    def single(cls, d: NepaliDate) -> DateRange: ...
    @classmethod
    def from_day_count(cls, start: NepaliDate, days: int) -> DateRange: ...
    @classmethod
    def month(cls, year: int, month: int) -> DateRange: ...
    @classmethod
    def year(cls, year: int) -> DateRange: ...
    @classmethod
    def current_month(cls, tz: datetime.tzinfo | None = None) -> DateRange: ...
    @classmethod
    def current_fiscal_year(cls, tz: datetime.tzinfo | None = None) -> DateRange: ...
    @classmethod
    def current_calendar_year(cls, tz: datetime.tzinfo | None = None) -> DateRange: ...

    start: NepaliDate
    end: NepaliDate

    def contains_range(self, other: DateRange) -> bool: ...
    def overlaps(self, other: DateRange) -> bool: ...
    def is_adjacent_to(self, other: DateRange) -> bool: ...
    def intersect(self, other: DateRange) -> DateRange | None: ...
    def union(self, other: DateRange) -> DateRange: ...
    def difference(self, other: DateRange) -> list[DateRange]: ...

    def split_by_month(self) -> list[DateRange]: ...
    def split_by_fiscal_quarter(self) -> list[DateRange]: ...
    def dates_with_interval(self, interval: int) -> list[NepaliDate]: ...
    def working_days(self, exclude_sunday: bool = False) -> list[NepaliDate]: ...
    def weekend_days(self, include_sunday: bool = True) -> list[NepaliDate]: ...

    def to_string(
        self,
        order: DateOrder = DateOrder.YMD,
        sep: Separator = Separator.SLASH,
        lang: Lang = Lang.EN
    ) -> str: ...
```

`from_day_count(start, days)` ends on `start + days - 1` and refuses a count below one.
`dates_with_interval` refuses an interval below one. `working_days` excludes Saturday and, when
asked, Sunday; `weekend_days` includes Saturday and, by default, Sunday. `str(range)` is the two
default displays separated by `" - "`, and `to_string(order, sep, lang)` is the same with the
short form options.

```python
>>> from nepdate import DateRange, NepaliDate
>>> r = DateRange.month(2081, 4)
>>> r.start, r.end
(NepaliDate(2081, 4, 1), NepaliDate(2081, 4, 32))
>>> len(r)
32
>>> NepaliDate(2081, 4, 15) in r
True
>>> r.contains_range(DateRange.single(NepaliDate(2081, 4, 15)))
True
>>> r.split_by_month()
[DateRange(NepaliDate(2081, 4, 1), NepaliDate(2081, 4, 32))]
>>> [str(piece) for piece in DateRange(NepaliDate(2081, 3, 30), NepaliDate(2081, 7, 2)).split_by_fiscal_quarter()]
['2081/03/30 - 2081/03/31', '2081/04/01 - 2081/06/30', '2081/07/01 - 2081/07/02']
>>> a = DateRange(NepaliDate(2081, 4, 10), NepaliDate(2081, 4, 20))
>>> a.intersect(DateRange(NepaliDate(2081, 4, 15), NepaliDate(2081, 4, 25)))
DateRange(NepaliDate(2081, 4, 15), NepaliDate(2081, 4, 20))
>>> [str(piece) for piece in a.difference(DateRange(NepaliDate(2081, 4, 13), NepaliDate(2081, 4, 17)))]
['2081/04/10 - 2081/04/12', '2081/04/18 - 2081/04/20']

```

Two ranges with the same bounds compare and hash equal. `repr` is the constructor form.

## 7. Fiscal year

A fiscal year starts on 1 Shrawan (month 4) and ends on the last day of Ashad (month 3) of the
following BS year. `FiscalYear` is named by its starting BS year, so FY 2081/82 is
`FiscalYear(2081)`. The quarters are Q1 Shrawan to Ashoj, Q2 Kartik to Poush, Q3 Magh to
Chaitra, and Q4 Baishakh to Ashad of the next year (D-08). `FiscalYear.containing(d)` picks the
value from a date, and `quarter_range(q)` gives the quarter as a range.

```text
class FiscalYear:
    def __init__(self, start_year: int) -> None: ...
    @classmethod
    def containing(cls, d: NepaliDate) -> FiscalYear: ...
    start_year: int
    def start(self) -> NepaliDate: ...
    def end(self) -> NepaliDate: ...
    def range(self) -> DateRange: ...
    def quarter_range(self, q: Quarter) -> DateRange: ...
    def label(self, lang: Lang = Lang.EN) -> str: ...

class NepaliDate:
    def fiscal_year(self) -> FiscalYear: ...
    def quarter(self) -> Quarter: ...

class Quarter(enum.IntEnum):
    Q1 = 1
    Q2 = 2
    Q3 = 3
    Q4 = 4

    def months(self) -> tuple[Month, Month, Month]: ...
```

```python
>>> from nepdate import FiscalYear, NepaliDate, Quarter
>>> fy = FiscalYear.containing(NepaliDate(2081, 4, 15))
>>> fy.label()
'2081/82'
>>> fy.start(), fy.end()
(NepaliDate(2081, 4, 1), NepaliDate(2082, 3, 32))
>>> fy.quarter_range(Quarter.Q1).start
NepaliDate(2081, 4, 1)
>>> Quarter.Q4.months()
(<Month.BAISHAKH: 1>, <Month.JESTHA: 2>, <Month.ASHAD: 3>)
>>> NepaliDate(2081, 4, 15).quarter()
<Quarter.Q1: 1>

```

`NepaliDate.fiscal_year()` returns `FiscalYear.containing(self)` and `NepaliDate.quarter()`
returns the quarter of the date.

## 8. Patro

The tithi, holiday and event data is a separate distribution, `nepdate-patro`, which depends on
the core (D-13). The core has no patro data and never imports `nepdate_patro`. `info(d)` returns
one `CalendarInfo` per day and never raises: a day outside the coverage returns one shared empty
value, not `None`. The data currently covers BS 2077-01-01 through 2084-08-20.

```text
from nepdate import DateRange, Lang, NepaliDate

class Tithi:
    np: str
    en: str
    def label(self, lang: Lang = Lang.EN) -> str: ...

class Event:
    np: str
    en: str
    def label(self, lang: Lang = Lang.EN) -> str: ...

class CalendarInfo:
    tithi: Tithi | None
    is_public_holiday: bool
    events: tuple[Event, ...]

def info(d: NepaliDate) -> CalendarInfo: ...
def coverage() -> DateRange: ...
def public_holidays() -> Iterator[NepaliDate]: ...
```

`coverage()` is the smallest range holding every day with data. `public_holidays()` yields the
gazetted dates in ascending order.

```python
>>> from nepdate import Lang, NepaliDate
>>> from nepdate_patro import coverage, info, public_holidays
>>> day = info(NepaliDate(2080, 5, 15))
>>> day.is_public_holiday
True
>>> day.tithi.label(Lang.EN)
'Dwitiya'
>>> [event.label(Lang.NE) for event in day.events]
['सापारु (गाईजात्रा) (काठमाडौँ बिदा)', 'रोपाईं जात्रा']
>>> coverage().start
NepaliDate(2077, 1, 1)
>>> first_holiday = next(public_holidays())
>>> first_holiday in coverage()
True

```

## Core only, by decision

These C# members have no Python equivalent, by the hub's decisions:

- The `autoAdjust` constructor and parse overloads (D-05, D-06). Use `parse` or
  `parse_lenient`.
- A default or empty `NepaliDate` and an empty `DateRange` (D-01). An invalid date cannot be
  constructed, and a range always holds at least one day.
- `CompareTo(object)` and `Equals(object)` overloads. Comparison is typed, and a foreign type
  returns `NotImplemented`.
- `IsLeapYear()` (D-12), replaced by `year_length`.
- The serialization object form, Newtonsoft, the XML serializer and `TypeConverter` (D-11).
  Use `isoformat`/`parse`, `to_json`/`from_json` and `to_ymd_int`/`from_ymd_int`.
- The `GetFiscalYear*(fiscalYear, month)` helpers (D-08). Use `FiscalYear` and `quarter_range`.
- The `weekday` numbering warning: Sunday is 0, not `datetime`'s Monday.

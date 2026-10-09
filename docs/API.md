# `nepdate` and `nepdate_patro` (Python): public API contract (v0.1)

The complete public surface (`__all__` of each package) for v0.1. Implement exactly this; a new
public name needs this file changed in the same PR, approved by the human. Behaviour:
`shared/spec/`. Conventions: ADR-0003. All types are immutable, hashable and use `__slots__`.

```python
# nepdate/__init__.py
MIN: NepaliDate                        # 1901-01-01
MAX: NepaliDate                        # 2199-12-30

class NepaliDate:
    def __init__(self, year: int, month: int, day: int) -> None: ...   # NepDateError(kind=...)
    @classmethod
    def from_date(cls, d: datetime.date) -> NepaliDate: ...            # datetime.datetime: its own .date()
    @classmethod
    def from_ordinal(cls, n: int) -> NepaliDate: ...                   # same ordinals as datetime.date
    @classmethod
    def today(cls, tz: datetime.tzinfo | None = None) -> NepaliDate: ...  # None: Asia/Kathmandu
    @classmethod
    def parse(cls, s: str) -> NepaliDate: ...                          # strict, PARSING §1
    @classmethod
    def parse_lenient(cls, s: str) -> NepaliDate: ...                  # PARSING §2

    year: int                          # read-only properties
    month: int                         # 1..12
    day: int
    @property
    def month_enum(self) -> Month: ...
    @property
    def weekday(self) -> Weekday: ...  # Sunday = 0 (not datetime's Monday = 0)
    @property
    def day_of_year(self) -> int: ...
    @property
    def month_length(self) -> int: ...
    def first_of_month(self) -> NepaliDate: ...
    def last_of_month(self) -> NepaliDate: ...
    def to_date(self) -> datetime.date: ...
    def to_ordinal(self) -> int: ...

    def add_days(self, n: int) -> NepaliDate: ...
    def add_months(self, n: int, overflow: Overflow = Overflow.CLAMP) -> NepaliDate: ...
    def add_years(self, n: int, overflow: Overflow = Overflow.CLAMP) -> NepaliDate: ...
    def days_until(self, other: NepaliDate) -> int: ...                # other - self (D-07)
    def diff(self, other: NepaliDate) -> DateDiff: ...                 # ALGORITHM §8a
    def __add__(self, td: datetime.timedelta) -> NepaliDate: ...       # whole days only
    def __sub__(self, other: NepaliDate | datetime.timedelta) -> datetime.timedelta | NepaliDate: ...
    # ==, <, <=, >, >=, hash: chronological; NotImplemented for other types

    def fiscal_year(self) -> FiscalYear: ...
    def quarter(self) -> Quarter: ...

    def __str__(self) -> str: ...       # "YYYY/MM/DD"
    def __repr__(self) -> str: ...      # "NepaliDate(2081, 4, 15)"
    def isoformat(self) -> str: ...     # "YYYY-MM-DD" (D-11)
    def short(self, order: DateOrder = DateOrder.YMD, sep: Separator = Separator.SLASH,
              pad: bool = True, lang: Lang = Lang.EN) -> str: ...
    def long(self, *, weekday: bool = False, year: bool = True, pad: bool = True,
             lang: Lang = Lang.EN) -> str: ...
    def format(self, pattern: str, lang: Lang = Lang.EN) -> str: ...   # FORMATTING §5
    def __format__(self, spec: str) -> str: ...                        # f"{d:dd MMMM yyyy}"; "" = str(d)

class Lang(enum.Enum):     EN = "en"; NE = "ne"
class Month(enum.IntEnum): BAISHAKH = 1; JESTHA = 2; ...; CHAITRA = 12
    def label(self, lang: Lang = Lang.EN) -> str: ...
    def short_label(self, lang: Lang = Lang.EN) -> str: ...            # D-04: Asa / Aso
class Weekday(enum.IntEnum): SUNDAY = 0; ...; SATURDAY = 6
    def label(self, lang: Lang = Lang.EN) -> str: ...
    def short_label(self, lang: Lang = Lang.EN) -> str: ...
class Overflow(enum.Enum): CLAMP = "clamp"; SPILL = "spill"           # ALGORITHM §8
class DateOrder(enum.Enum): YMD, YDM, MYD, MDY, DYM, DMY
class Separator(enum.Enum): SLASH = "/"; BACKSLASH = "\\"; DOT = "."; UNDERSCORE = "_"; DASH = "-"; SPACE = " "

def to_nepali_digits(n: int, min_width: int = 0) -> str: ...

class ErrorKind(enum.Enum):
    OUT_OF_RANGE; INVALID_MONTH; INVALID_DAY; INVALID_GREGORIAN
    INVALID_CHARACTER; WRONG_GROUP_COUNT; NUMBER_TOO_LONG; AMBIGUOUS; UNRECOGNIZED
class NepDateError(ValueError):
    kind: ErrorKind

@dataclasses.dataclass(frozen=True, slots=True)
class DateDiff: negative: bool; years: int; months: int; days: int; total_days: int

class FiscalYear:                       # starting BS year: FY 2082/83 = FiscalYear(2082)
    def __init__(self, start_year: int) -> None: ...
    start_year: int
    @classmethod
    def containing(cls, d: NepaliDate) -> FiscalYear: ...
    def start(self) -> NepaliDate: ...
    def end(self) -> NepaliDate: ...
    def range(self) -> DateRange: ...
    def quarter_range(self, q: Quarter) -> DateRange: ...
    def label(self, lang: Lang = Lang.EN) -> str: ...                  # "2082/83" / "२०८२/८३"
class Quarter(enum.IntEnum): Q1 = 1; Q2 = 2; Q3 = 3; Q4 = 4
    def months(self) -> tuple[Month, Month, Month]: ...

class DateRange:                        # inclusive; D-09: no set operations
    def __init__(self, start: NepaliDate, end: NepaliDate) -> None: ...  # NepDateError if start > end
    @classmethod
    def month(cls, year: int, month: int) -> DateRange: ...
    @classmethod
    def year(cls, year: int) -> DateRange: ...
    start: NepaliDate
    end: NepaliDate
    def __len__(self) -> int: ...
    def __contains__(self, d: object) -> bool: ...
    def __iter__(self) -> Iterator[NepaliDate]: ...
    def __reversed__(self) -> Iterator[NepaliDate]: ...
```

```python
# nepdate_patro/__init__.py  (distribution nepdate-patro, ADR-0001 §1; a separate install)
# Usage: from nepdate_patro import info, coverage, public_holidays
from nepdate import DateRange, Lang, NepaliDate

@dataclasses.dataclass(frozen=True, slots=True)
class Tithi: np: str; en: str
    def label(self, lang: Lang = Lang.EN) -> str: ...  # np for Lang.NE, en for Lang.EN
@dataclasses.dataclass(frozen=True, slots=True)
class Event: np: str; en: str
    def label(self, lang: Lang = Lang.EN) -> str: ...
@dataclasses.dataclass(frozen=True, slots=True)
class CalendarInfo: tithi: Tithi | None; is_public_holiday: bool; events: tuple[Event, ...]
def info(d: NepaliDate) -> CalendarInfo: ...     # PATRO §2; never raises; empty outside coverage;
                                                 # returns a shared prebuilt object (ADR-0002 §6)
def coverage() -> DateRange: ...                 # 2077-01-01..2084-08-20 with today's data
def public_holidays() -> Iterator[NepaliDate]: ...  # ascending, 294 dates with today's data
```

The core `nepdate` package has no patro names and never imports `nepdate_patro`.

Notes:
- `d - other_date` returns a `timedelta` (Python interop, like `datetime.date`); `days_until` is the
  spec's signed integer (D-07). Both come from the same serial difference.
- `today()` defaults to Nepal time, not the host's zone, because a UTC server is 5 h 45 min behind.
- Weekday numbering is the spec's (Sunday = 0). The docstring warns that `datetime.date.weekday()`
  uses Monday = 0.

"""NepaliDate: a Bikram Sambat date, immutable and hashable."""

from __future__ import annotations

import datetime
import operator

from ._calendar import (
    BUCKET,
    MAX_YEAR,
    MIN_YEAR,
    MONTH_LENGTHS,
    MONTH_NUM,
    MONTH_START_ORD,
    MONTH_YEAR,
)
from ._diff import DateDiff
from ._errors import ErrorKind, NepDateError
from ._format import format_default, format_iso, format_long, format_short
from ._names import DateOrder, Lang, Month, Overflow, Quarter, Separator, Weekday
from ._parse import parse_lenient, parse_strict
from ._pattern import format_pattern

# `typing` would add three modules to `import nepdate` (the import gate); type checkers treat a
# module-level TYPE_CHECKING constant the same as typing.TYPE_CHECKING.
TYPE_CHECKING = False
if TYPE_CHECKING:
    from ._fiscal import FiscalYear

_TOTAL_DAYS = MONTH_START_ORD[-1] - MONTH_START_ORD[0]
_TOTAL_MONTHS = len(MONTH_LENGTHS)


class NepaliDate:
    """A date in the Bikram Sambat calendar, from 1901-01-01 to 2199-12-30.

    Immutable and hashable. Comparisons and hashing use the proleptic Gregorian ordinal
    (``_o``), so dates order chronologically. The private slots are read-only by
    convention only: code that reaches into ``_y`` can overwrite them, accepted for
    speed (ADR-0002 §2).
    """

    __slots__ = ("_d", "_m", "_o", "_y")

    def __init__(self, year: int, month: int, day: int) -> None:
        if type(year) is int and type(month) is int and type(day) is int:
            y = year
            m = month
            d = day
        else:
            for value in (year, month, day):
                if isinstance(value, bool):
                    raise TypeError(
                        f"NepaliDate arguments must be integers, not {type(value).__name__}"
                    )
            y = operator.index(year)
            m = operator.index(month)
            d = operator.index(day)
        if y < MIN_YEAR or y > MAX_YEAR:
            raise NepDateError(
                ErrorKind.OUT_OF_RANGE, f"year {y} is outside {MIN_YEAR}..{MAX_YEAR}"
            )
        if m < Month.BAISHAKH or m > Month.CHAITRA:
            raise NepDateError(ErrorKind.INVALID_MONTH, f"month {m} is outside 1..12")
        length = MONTH_LENGTHS[(y - MIN_YEAR) * 12 + (m - 1)]
        if d < 1 or d > length:
            raise NepDateError(ErrorKind.INVALID_DAY, f"day {d} is outside 1..{length}")
        self._y = y
        self._m = m
        self._d = d
        self._o = MONTH_START_ORD[(y - MIN_YEAR) * 12 + (m - 1)] + d - 1

    @property
    def year(self) -> int:
        """The BS year."""
        return self._y

    @property
    def month(self) -> int:
        """The BS month, 1 through 12."""
        return self._m

    @property
    def day(self) -> int:
        """The BS day of the month."""
        return self._d

    @property
    def month_enum(self) -> Month:
        """The BS month as a ``Month``."""
        return Month(self._m)

    @property
    def weekday(self) -> Weekday:
        """The day of the week, Sunday = 0 (not datetime's Monday = 0)."""
        return Weekday(self._o % 7)

    @property
    def day_of_year(self) -> int:
        """The 1-based day within the BS year."""
        return self._o - MONTH_START_ORD[(self._y - MIN_YEAR) * 12] + 1

    @property
    def month_length(self) -> int:
        """The number of days in the month of this date."""
        return MONTH_LENGTHS[(self._y - MIN_YEAR) * 12 + (self._m - 1)]

    def first_of_month(self) -> NepaliDate:
        """The first day of the month of this date."""
        return _from_parts(self._y, self._m, 1, self._o - self._d + 1)

    def last_of_month(self) -> NepaliDate:
        """The last day of the month of this date."""
        length = self.month_length
        return _from_parts(self._y, self._m, length, self._o - self._d + length)

    def to_date(self) -> datetime.date:
        """The proleptic Gregorian date of this date, as a ``datetime.date``."""
        return datetime.date.fromordinal(self._o)

    def to_ordinal(self) -> int:
        """The proleptic Gregorian ordinal, shared with ``datetime.date``."""
        return self._o

    @classmethod
    def from_date(cls, d: datetime.date) -> NepaliDate:
        """Build the BS date of a ``datetime.date`` (or ``datetime``, using its date part).

        Args:
            d: The Gregorian date. An aware ``datetime`` uses its own ``.date()``; callers
                that mean "the date in Nepal" must convert to ``Asia/Kathmandu`` first.

        Returns:
            The matching BS date.

        Raises:
            NepDateError: The date is outside 1844-04-11 through 2143-04-15.
        """
        return cls.from_ordinal(d.toordinal())

    @classmethod
    def from_ordinal(cls, n: int) -> NepaliDate:
        """Build the BS date for a proleptic Gregorian ordinal.

        Args:
            n: The ordinal, as used by ``datetime.date.toordinal()``.

        Returns:
            The matching BS date.

        Raises:
            NepDateError: The ordinal is outside the supported range.
        """
        k = n - MONTH_START_ORD[0]
        if k < 0 or k >= _TOTAL_DAYS:
            raise NepDateError(ErrorKind.OUT_OF_RANGE, f"ordinal {n} is outside the range")
        return _from_serial(n)

    @classmethod
    def today(cls, tz: datetime.tzinfo | None = None) -> NepaliDate:
        """The current date in ``tz``; None means Nepal time (ADR-0003).

        Args:
            tz: The time zone to read the clock in.

        Returns:
            The current BS date.

        Raises:
            NepDateError: The clock is outside 1844-04-11 through 2143-04-15.
        """
        return _today_from(_now(), tz, cls)

    @classmethod
    def parse(cls, s: str) -> NepaliDate:
        """Parse a date from the strict form of PARSING §1.

        Args:
            s: The text, year then month then day, in ASCII or Devanagari digits.

        Returns:
            The parsed date.

        Raises:
            NepDateError: The text is malformed or names an invalid date.
        """
        return parse_strict(s, cls)

    @classmethod
    def parse_lenient(cls, s: str) -> NepaliDate:
        """Parse human-written text with the lenient rules of PARSING §2.

        Args:
            s: Text such as ``"15 Shrawan 2080"``, ``"2080/04/15 BS"`` or ``"१५ साउन २०८०"``.

        Returns:
            The parsed date.

        Raises:
            NepDateError: No rule matches or the date is invalid.
        """
        return parse_lenient(s, cls)

    def add_days(self, n: int) -> NepaliDate:
        """The date ``n`` days from this one, by ordinal addition.

        Args:
            n: The whole number of days to add; a negative value subtracts.

        Returns:
            The resulting date.

        Raises:
            NepDateError: The result is outside 1901-01-01 through 2199-12-30.
        """
        return self.from_ordinal(self._o + n)

    def days_until(self, other: NepaliDate) -> int:
        """The signed day count from this date to ``other`` (``other - self``, D-07).

        Args:
            other: The date to count towards.

        Returns:
            ``other.to_ordinal() - self.to_ordinal()``.
        """
        return other._o - self._o

    def add_months(self, n: int, overflow: Overflow = Overflow.CLAMP) -> NepaliDate:
        """The date ``n`` months from this one (ALGORITHM §8).

        Args:
            n: The whole number of months to add; a negative value subtracts.
            overflow: CLAMP caps the day at the target month's length; SPILL carries
                the leftover days into the next month.

        Returns:
            The resulting date.

        Raises:
            NepDateError: The result is outside the supported range.
        """
        total = (self._y - MIN_YEAR) * 12 + (self._m - 1) + n
        if total < 0 or total >= _TOTAL_MONTHS:
            raise NepDateError(ErrorKind.OUT_OF_RANGE, f"month offset {n} is outside the range")
        year, month0 = divmod(total, 12)
        year += MIN_YEAR
        month = month0 + 1
        index = (year - MIN_YEAR) * 12 + (month - 1)
        length = MONTH_LENGTHS[index]
        if self._d <= length:
            return _from_parts(year, month, self._d, MONTH_START_ORD[index] + self._d - 1)
        if overflow is Overflow.SPILL:
            if month == Month.CHAITRA:
                year += 1
                month = 1
            else:
                month += 1
            if year > MAX_YEAR:
                raise NepDateError(
                    ErrorKind.OUT_OF_RANGE, f"month offset {n} spills past the range"
                )
            index = (year - MIN_YEAR) * 12 + (month - 1)
            day = self._d - length
            return _from_parts(year, month, day, MONTH_START_ORD[index] + day - 1)
        return _from_parts(year, month, length, MONTH_START_ORD[index] + length - 1)

    def add_years(self, n: int, overflow: Overflow = Overflow.CLAMP) -> NepaliDate:
        """The date ``n`` years from this one, as ``add_months(12 * n)``.

        Args:
            n: The whole number of years to add; a negative value subtracts.
            overflow: CLAMP caps the day at the target month's length; SPILL carries
                the leftover days into the next month.

        Returns:
            The resulting date.

        Raises:
            NepDateError: The result is outside the supported range.
        """
        return self.add_months(n * 12, overflow)

    def diff(self, other: NepaliDate) -> DateDiff:
        """The calendar breakdown between this date and ``other`` (ALGORITHM §8a).

        Args:
            other: The date to diff against.

        Returns:
            The signed years, months and days, plus the total day difference.
        """
        if self <= other:
            a, b = self, other
            negative = False
        else:
            a, b = other, self
            negative = True
        months = (b._y - a._y) * 12 + (b._m - a._m)
        anchor = a.add_months(months)
        if anchor > b:
            months -= 1
            anchor = a.add_months(months)
        return DateDiff(
            negative=negative,
            years=months // 12,
            months=months % 12,
            days=b._o - anchor._o,
            total_days=self.days_until(other),
        )

    def fiscal_year(self) -> FiscalYear:
        """The fiscal year containing this date (ALGORITHM §8b)."""
        from ._fiscal import FiscalYear  # noqa: PLC0415 - _fiscal imports this module at load

        return FiscalYear.containing(self)

    def quarter(self) -> Quarter:
        """The fiscal quarter of this date (ALGORITHM §8b)."""
        if Month.SHRAWAN <= self._m <= Month.ASHOJ:
            return Quarter.Q1
        if Month.KARTIK <= self._m <= Month.POUSH:
            return Quarter.Q2
        if Month.MAGH <= self._m <= Month.CHAITRA:
            return Quarter.Q3
        return Quarter.Q4

    def __str__(self) -> str:
        """The default display, ``YYYY/MM/DD`` with ASCII digits."""
        return format_default(self._y, self._m, self._d, Lang.EN)

    def __repr__(self) -> str:
        """The unambiguous constructor form, for example ``NepaliDate(2081, 4, 15)``."""
        return f"NepaliDate({self._y}, {self._m}, {self._d})"

    def isoformat(self) -> str:
        """The sortable ``YYYY-MM-DD`` form (D-11)."""
        return format_iso(self._y, self._m, self._d, Lang.EN)

    def short(
        self,
        order: DateOrder = DateOrder.YMD,
        sep: Separator = Separator.SLASH,
        pad: bool = True,
        lang: Lang = Lang.EN,
    ) -> str:
        """The short form of FORMATTING §3.

        Args:
            order: The field order; the default is year, month, day.
            sep: The separator between the fields.
            pad: Whether month and day are two digits.
            lang: The language of the digits.

        Returns:
            The short form, for example ``"2080-05-15"`` or ``"१५-५-२०८०"``.
        """
        return format_short(self._y, self._m, self._d, order, sep, pad, lang)

    def long(
        self,
        *,
        weekday: bool = False,
        year: bool = True,
        pad: bool = True,
        lang: Lang = Lang.EN,
    ) -> str:
        """The long form of FORMATTING §4.

        Args:
            weekday: Whether to start with the weekday name.
            year: Whether to end with the year.
            pad: Whether the day is two digits.
            lang: The language of the names and digits.

        Returns:
            The long form, for example ``"Tuesday, Shrawan 15, 2081"``.
        """
        return format_long(
            self._y,
            self._m,
            self._d,
            self._o % 7,
            with_weekday=weekday,
            include_year=year,
            pad=pad,
            lang=lang,
        )

    def format(self, pattern: str, lang: Lang = Lang.EN) -> str:
        """Format this date with a standard or custom pattern (FORMATTING §5).

        Args:
            pattern: ``""``, ``G``, ``g`` or ``d`` for the default display, ``D`` for the long
                form, ``s`` for ``YYYY-MM-DD``, or a custom pattern such as ``"dd MMMM yyyy"``.
            lang: The language of the names and digits.

        Returns:
            The formatted date; literal characters are never localised.
        """
        return format_pattern(pattern, self._y, self._m, self._d, self._o % 7, lang)

    def __format__(self, spec: str) -> str:
        """Format for f-strings and ``str.format``; an empty spec is ``str``.

        Args:
            spec: The format spec, interpreted as a FORMATTING §5 pattern.

        Returns:
            The formatted date in English.
        """
        if spec == "":
            return str(self)
        return self.format(spec)

    def __add__(self, td: datetime.timedelta) -> NepaliDate:
        """Add a whole-day timedelta, like ``datetime.date + timedelta``.

        Args:
            td: The amount to add; it must be a whole number of days.

        Returns:
            The resulting date.

        Raises:
            NepDateError: ``td`` has a fractional day, or the result is out of range.
        """
        if not isinstance(td, datetime.timedelta):
            return NotImplemented
        if td.seconds or td.microseconds:
            raise NepDateError(ErrorKind.OUT_OF_RANGE, "timedelta must be a whole number of days")
        return self.add_days(td.days)

    def __sub__(self, other: NepaliDate | datetime.timedelta) -> datetime.timedelta | NepaliDate:
        """Subtract a date (to a timedelta) or a whole-day timedelta (to a date).

        Args:
            other: Another date, or a whole-day timedelta.

        Returns:
            ``self - other`` as a timedelta when ``other`` is a date, or the date
            ``self + (-other)`` when ``other`` is a timedelta.

        Raises:
            NepDateError: A timedelta with a fractional day, or an out-of-range result.
        """
        if isinstance(other, NepaliDate):
            return datetime.timedelta(days=self._o - other._o)
        if isinstance(other, datetime.timedelta):
            return self + (-other)
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NepaliDate):
            return NotImplemented
        return self._o == other._o

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, NepaliDate):
            return NotImplemented
        return self._o < other._o

    def __le__(self, other: object) -> bool:
        if not isinstance(other, NepaliDate):
            return NotImplemented
        return self._o <= other._o

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, NepaliDate):
            return NotImplemented
        return self._o > other._o

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, NepaliDate):
            return NotImplemented
        return self._o >= other._o

    def __hash__(self) -> int:
        return hash(self._o)


def _from_serial(n: int) -> NepaliDate:
    """Build a date from an in-range ordinal without re-checking the range.

    Args:
        n: A proleptic Gregorian ordinal inside the supported range.

    Returns:
        The matching date.
    """
    k = n - MONTH_START_ORD[0]
    i = BUCKET[k >> 5]
    if n >= MONTH_START_ORD[i + 1]:
        i += 1
    if n >= MONTH_START_ORD[i + 1]:
        i += 1
    return _from_parts(MONTH_YEAR[i], MONTH_NUM[i], n - MONTH_START_ORD[i] + 1, n)


def _from_parts(year: int, month: int, day: int, ordinal: int) -> NepaliDate:
    """Build a validated date from its four fields without re-checking them.

    Args:
        year: The BS year.
        month: The BS month, 1 through 12.
        day: The BS day.
        ordinal: The proleptic Gregorian ordinal of the date.

    Returns:
        The new date.
    """
    date = object.__new__(NepaliDate)
    date._y = year
    date._m = month
    date._d = day
    date._o = ordinal
    return date


MIN = _from_parts(MIN_YEAR, Month.BAISHAKH, 1, MONTH_START_ORD[0])
MAX = _from_parts(MAX_YEAR, Month.CHAITRA, MONTH_LENGTHS[-1], MONTH_START_ORD[-1] - 1)


def _now() -> datetime.datetime:
    """Return the current UTC instant; tests replace this to inject a clock."""
    return datetime.datetime.now(datetime.UTC)


def _today_from(
    now: datetime.datetime, tz: datetime.tzinfo | None, date_type: type[NepaliDate]
) -> NepaliDate:
    """Convert an injected instant to a BS date in ``tz``.

    Args:
        now: An aware instant.
        tz: The zone to convert to; None means ``Asia/Kathmandu``.
        date_type: The ``NepaliDate`` class.

    Returns:
        The BS date of ``now`` in ``tz``.

    Raises:
        NepDateError: The date is outside the supported range.
    """
    if tz is None:
        # Imported here so `import nepdate` stays inside the ADR-0004 gate 5 allowlist.
        from zoneinfo import ZoneInfo  # noqa: PLC0415

        tz = ZoneInfo("Asia/Kathmandu")
    return date_type.from_date(now.astimezone(tz).date())

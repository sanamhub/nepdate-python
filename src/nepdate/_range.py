"""DateRange: an inclusive span of NepaliDate values and the operations on it."""

from __future__ import annotations

import datetime

from ._date import NepaliDate, _from_serial
from ._errors import ErrorKind, NepDateError
from ._names import DateOrder, Lang, Month, Separator, Weekday

# `collections.abc` is not loaded at startup on Python 3.11 and 3.12, so importing it here broke
# the import gate there; the annotation needs it only for the type checker, as in `_date.py`.
TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Iterator


class DateRange:
    """An inclusive range of Bikram Sambat dates.

    The two bounds are dates, and a range always holds at least one day: a start after the
    end is refused, so a range can never be empty (D-01).

    Examples:
        >>> len(DateRange.month(2080, 5))
        31
        >>> DateRange.month(2080, 5).start
        NepaliDate(2080, 5, 1)
    """

    __slots__ = ("_end", "_start")

    def __init__(self, start: NepaliDate, end: NepaliDate) -> None:
        if start > end:
            raise NepDateError(ErrorKind.OUT_OF_RANGE, "start is after end")
        self._start = start
        self._end = end

    @property
    def start(self) -> NepaliDate:
        """The first day of the range."""
        return self._start

    @property
    def end(self) -> NepaliDate:
        """The last day of the range."""
        return self._end

    def __len__(self) -> int:
        """The number of days in the range, computed from the ordinals."""
        return self._end.to_ordinal() - self._start.to_ordinal() + 1

    def __contains__(self, d: object) -> bool:
        """Whether ``d`` is a date within the range, inclusive."""
        if not isinstance(d, NepaliDate):
            return False
        return self._start <= d <= self._end

    def __iter__(self) -> Iterator[NepaliDate]:
        """Yield every day from start to end, built from serials."""
        ordinal = self._start.to_ordinal()
        end = self._end.to_ordinal()
        while ordinal <= end:
            yield _from_serial(ordinal)
            ordinal += 1

    def __reversed__(self) -> Iterator[NepaliDate]:
        """Yield every day from end to start, built from serials."""
        ordinal = self._end.to_ordinal()
        start = self._start.to_ordinal()
        while ordinal >= start:
            yield _from_serial(ordinal)
            ordinal -= 1

    @classmethod
    def single(cls, d: NepaliDate) -> DateRange:
        """The one-day range of ``d``.

        Args:
            d: The day.

        Returns:
            A range whose start and end are both ``d``.
        """
        return cls(d, d)

    @classmethod
    def from_day_count(cls, start: NepaliDate, days: int) -> DateRange:
        """The range of ``days`` days from ``start``, both ends included.

        Args:
            start: The first day.
            days: The number of days; it must be at least 1.

        Returns:
            ``start`` through ``start + days - 1``.

        Raises:
            NepDateError: ``days`` is below 1, or the end is outside the supported range.
        """
        if days < 1:
            raise NepDateError(ErrorKind.OUT_OF_RANGE, f"day count {days} is below 1")
        return cls(start, start.add_days(days - 1))

    @classmethod
    def month(cls, year: int, month: int) -> DateRange:
        """The range of one BS month.

        Args:
            year: The BS year.
            month: The BS month, 1 through 12.

        Returns:
            The month as a range.

        Raises:
            NepDateError: The year or month is invalid.
        """
        first = NepaliDate(year, month, 1)
        return cls(first, first.last_of_month())

    @classmethod
    def year(cls, year: int) -> DateRange:
        """The range of one BS year.

        Args:
            year: The BS year.

        Returns:
            The year as a range.

        Raises:
            NepDateError: The year is invalid.
        """
        return cls(NepaliDate(year, 1, 1), NepaliDate(year, 12, 1).last_of_month())

    @classmethod
    def current_month(cls, tz: datetime.tzinfo | None = None) -> DateRange:
        """The month range that contains today in ``tz``.

        Args:
            tz: The time zone to read the clock in; None means Nepal time, as in
                ``NepaliDate.today``.

        Returns:
            The current BS month.

        Raises:
            NepDateError: The clock is outside the supported range.
        """
        today = NepaliDate.today(tz)
        return cls.month(today.year, today.month)

    @classmethod
    def current_fiscal_year(cls, tz: datetime.tzinfo | None = None) -> DateRange:
        """The fiscal year range that contains today in ``tz``.

        Args:
            tz: The time zone to read the clock in; None means Nepal time, as in
                ``NepaliDate.today``.

        Returns:
            The current fiscal year, 1 Shrawan through the end of Ashad.

        Raises:
            NepDateError: The clock is outside the supported range.
        """
        from ._fiscal import FiscalYear  # noqa: PLC0415 - _fiscal imports this module at load

        return FiscalYear.containing(NepaliDate.today(tz)).range()

    @classmethod
    def current_calendar_year(cls, tz: datetime.tzinfo | None = None) -> DateRange:
        """The BS calendar year range that contains today in ``tz``.

        Args:
            tz: The time zone to read the clock in; None means Nepal time, as in
                ``NepaliDate.today``.

        Returns:
            The current BS year.

        Raises:
            NepDateError: The clock is outside the supported range.
        """
        return cls.year(NepaliDate.today(tz).year)

    def contains_range(self, other: DateRange) -> bool:
        """Whether ``other`` lies entirely inside this range.

        Args:
            other: The range to test.

        Returns:
            True when every day of ``other`` is in this range.
        """
        return self._start <= other._start and other._end <= self._end

    def overlaps(self, other: DateRange) -> bool:
        """Whether this range and ``other`` share at least one day.

        Args:
            other: The range to test.

        Returns:
            True when the two ranges intersect.
        """
        return self._start <= other._end and other._start <= self._end

    def is_adjacent_to(self, other: DateRange) -> bool:
        """Whether one range starts the day after the other ends (D-16).

        Args:
            other: The range to test.

        Returns:
            True when the ranges touch without overlapping. A range that ends at the last
            supported day has no neighbour after it, so the answer is False rather than an
            error.
        """
        return (
            self._end.to_ordinal() + 1 == other._start.to_ordinal()
            or other._end.to_ordinal() + 1 == self._start.to_ordinal()
        )

    def intersect(self, other: DateRange) -> DateRange | None:
        """The days both ranges hold, or None when they do not overlap (D-16).

        Args:
            other: The range to intersect with.

        Returns:
            The overlapping range, or None when the ranges are disjoint.
        """
        start = self._start if self._start > other._start else other._start
        end = self._end if self._end < other._end else other._end
        if start > end:
            return None
        return DateRange(start, end)

    def union(self, other: DateRange) -> DateRange:
        """The smallest range covering both.

        Args:
            other: The other range.

        Returns:
            A range from the earlier start to the later end.
        """
        start = self._start if self._start < other._start else other._start
        end = self._end if self._end > other._end else other._end
        return DateRange(start, end)

    def difference(self, other: DateRange) -> list[DateRange]:
        """This range with ``other`` removed.

        Args:
            other: The range to remove.

        Returns:
            No range when ``other`` covers this one, one range when the removal touches an
            end or misses entirely, or two ranges when ``other`` is in the middle.
        """
        if not self.overlaps(other):
            return [self]
        parts: list[DateRange] = []
        if self._start < other._start:
            parts.append(DateRange(self._start, other._start.add_days(-1)))
        if other._end < self._end:
            parts.append(DateRange(other._end.add_days(1), self._end))
        return parts

    def split_by_month(self) -> list[DateRange]:
        """One range per BS month this range touches, clipped at the ends (D-16).

        Returns:
            The pieces in date order. The last piece ends at this range's end, including
            when that end is the last supported day.
        """
        pieces: list[DateRange] = []
        year = self._start.year
        month = self._start.month
        while True:
            piece = DateRange.month(year, month)
            start = piece.start if piece.start > self._start else self._start
            end = piece.end if piece.end < self._end else self._end
            pieces.append(DateRange(start, end))
            if piece.end >= self._end:
                return pieces
            month += 1
            if month > Month.CHAITRA:
                month = Month.BAISHAKH
                year += 1

    def split_by_fiscal_quarter(self) -> list[DateRange]:
        """One range per fiscal quarter this range touches, clipped at the ends (D-16).

        Fiscal quarters run Q1 Shrawan to Ashoj, Q2 Kartik to Poush, Q3 Magh to Chaitra
        and Q4 Baishakh to Ashad of the following BS year.

        Returns:
            The pieces in date order. The last piece ends at this range's end, including
            when that end is the last supported day.
        """
        from ._fiscal import FiscalYear  # noqa: PLC0415 - _fiscal imports this module at load

        pieces: list[DateRange] = []
        current = self._start
        while True:
            quarter = FiscalYear.containing(current).quarter_range(current.quarter())
            start = quarter.start if quarter.start > self._start else self._start
            end = quarter.end if quarter.end < self._end else self._end
            pieces.append(DateRange(start, end))
            if quarter.end >= self._end:
                return pieces
            current = quarter.end.add_days(1)

    def dates_with_interval(self, interval: int) -> list[NepaliDate]:
        """Every ``interval`` days from the start, both bounds included (D-16).

        Args:
            interval: The step in days; it must be at least 1.

        Returns:
            The dates in order, starting with this range's start. The last supported day
            is included when the step lands on it.

        Raises:
            NepDateError: ``interval`` is below 1.
        """
        if interval < 1:
            raise NepDateError(ErrorKind.OUT_OF_RANGE, f"interval {interval} is below 1")
        start = self._start.to_ordinal()
        end = self._end.to_ordinal()
        return [_from_serial(ordinal) for ordinal in range(start, end + 1, interval)]

    def working_days(self, exclude_sunday: bool = False) -> list[NepaliDate]:
        """Every day except Saturday, and except Sunday when asked (D-16).

        Args:
            exclude_sunday: Whether Sunday is a non-working day too.

        Returns:
            The working days in date order. The last supported day is included when it is
            a working day.
        """
        start = self._start.to_ordinal()
        end = self._end.to_ordinal()
        days: list[NepaliDate] = []
        for ordinal in range(start, end + 1):
            weekday = ordinal % 7
            if weekday == Weekday.SATURDAY:
                continue
            if exclude_sunday and weekday == Weekday.SUNDAY:
                continue
            days.append(_from_serial(ordinal))
        return days

    def weekend_days(self, include_sunday: bool = True) -> list[NepaliDate]:
        """Every Saturday, and Sunday when asked (D-16).

        Args:
            include_sunday: Whether Sunday is a weekend day too.

        Returns:
            The weekend days in date order. The last supported day is included when it is
            a weekend day.
        """
        start = self._start.to_ordinal()
        end = self._end.to_ordinal()
        days: list[NepaliDate] = []
        for ordinal in range(start, end + 1):
            weekday = ordinal % 7
            if weekday == Weekday.SATURDAY or (include_sunday and weekday == Weekday.SUNDAY):
                days.append(_from_serial(ordinal))
        return days

    def __str__(self) -> str:
        """The default form, the two default displays separated by ``" - "``."""
        return f"{self._start} - {self._end}"

    def __repr__(self) -> str:
        """The constructor form, for example ``DateRange(NepaliDate(2081, 4, 1), ...)``."""
        return f"DateRange({self._start!r}, {self._end!r})"

    def to_string(
        self,
        order: DateOrder = DateOrder.YMD,
        sep: Separator = Separator.SLASH,
        lang: Lang = Lang.EN,
    ) -> str:
        """The two dates in one short form, separated by ``" - "``.

        Args:
            order: The field order of both dates.
            sep: The separator between the fields.
            lang: The language of the digits.

        Returns:
            The short form of the start, then ``" - "``, then the short form of the end.
        """
        start = self._start.short(order, sep, lang=lang)
        end = self._end.short(order, sep, lang=lang)
        return f"{start} - {end}"

    def __eq__(self, other: object) -> bool:
        """Whether ``other`` is a range with the same two bounds."""
        if not isinstance(other, DateRange):
            return NotImplemented
        return self._start == other._start and self._end == other._end

    def __hash__(self) -> int:
        """The hash of the two bounds, so equal ranges hash equal."""
        return hash((self._start, self._end))

"""DateRange: an inclusive span of NepaliDate values (D-09: no set operations)."""

from __future__ import annotations

from collections.abc import Iterator

from ._date import NepaliDate, _from_serial
from ._errors import ErrorKind, NepDateError


class DateRange:
    """An inclusive range of Bikram Sambat dates.

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

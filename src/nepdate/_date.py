"""NepaliDate: a Bikram Sambat date, immutable and hashable."""

from __future__ import annotations

import operator

from ._calendar import MAX_YEAR, MIN_YEAR, MONTH_LENGTHS, MONTH_START_ORD
from ._errors import ErrorKind, NepDateError
from ._names import Month


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

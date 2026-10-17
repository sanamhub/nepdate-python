"""FiscalYear: Nepal's Shrawan-to-Ashad fiscal calendar (ALGORITHM §8b)."""

from __future__ import annotations

from ._calendar import MAX_YEAR, MIN_YEAR, MONTH_LENGTHS, MONTH_START_ORD
from ._date import NepaliDate, _from_parts
from ._errors import ErrorKind, NepDateError
from ._names import Lang, Month, Quarter
from ._range import DateRange

_MIN_FY = MIN_YEAR - 1
_MAX_FY = MAX_YEAR

_NEPALI_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")
_YEARS_NE = tuple(str(year).translate(_NEPALI_DIGITS) for year in range(_MIN_FY, _MAX_FY + 1))
_TWO_DIGIT_NE = tuple(f"{n:02d}".translate(_NEPALI_DIGITS) for n in range(100))


class FiscalYear:
    """A Nepali fiscal year, named by its starting BS year (FY 2082/83 = FiscalYear(2082))."""

    __slots__ = ("_start_year",)

    def __init__(self, start_year: int) -> None:
        if start_year < _MIN_FY or start_year > _MAX_FY:
            raise NepDateError(
                ErrorKind.OUT_OF_RANGE, f"fiscal year {start_year} is outside the range"
            )
        self._start_year = start_year

    @property
    def start_year(self) -> int:
        """The BS year the fiscal year starts in."""
        return self._start_year

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FiscalYear):
            return NotImplemented
        return self._start_year == other._start_year

    def __hash__(self) -> int:
        return hash(self._start_year)

    @classmethod
    def containing(cls, d: NepaliDate) -> FiscalYear:
        """The fiscal year that contains ``d``.

        Args:
            d: The date to locate.

        Returns:
            The fiscal year; a date before Shrawan belongs to the previous fiscal year.
        """
        return cls(d.year if d.month >= Month.SHRAWAN else d.year - 1)

    def start(self) -> NepaliDate:
        """The first day, 1 Shrawan.

        Raises:
            NepDateError: The start is before the supported range.
        """
        if self._start_year < MIN_YEAR:
            raise NepDateError(ErrorKind.OUT_OF_RANGE, "fiscal year starts before the range")
        index = (self._start_year - MIN_YEAR) * 12 + (Month.SHRAWAN - 1)
        return _from_parts(self._start_year, Month.SHRAWAN, 1, MONTH_START_ORD[index])

    def end(self) -> NepaliDate:
        """The last day, the end of Ashad of the following year.

        Raises:
            NepDateError: The end is after the supported range.
        """
        year = self._start_year + 1
        if year > MAX_YEAR:
            raise NepDateError(ErrorKind.OUT_OF_RANGE, "fiscal year ends after the range")
        index = (year - MIN_YEAR) * 12 + (Month.ASHAD - 1)
        day = MONTH_LENGTHS[index]
        return _from_parts(year, Month.ASHAD, day, MONTH_START_ORD[index] + day - 1)

    def range(self) -> DateRange:
        """The whole fiscal year as a DateRange."""
        return DateRange(self.start(), self.end())

    def quarter_range(self, q: Quarter) -> DateRange:
        """The DateRange of one quarter of this fiscal year.

        Args:
            q: The quarter.

        Returns:
            The quarter as a range.

        Raises:
            NepDateError: The quarter lies outside the supported range.
        """
        if q is Quarter.Q4:
            start_year = self._start_year + 1
            start_month = Month.BAISHAKH
        else:
            start_year = self._start_year
            start_month = Month((q.value - 1) * 3 + 4)
        if start_year < MIN_YEAR or start_year > MAX_YEAR:
            raise NepDateError(ErrorKind.OUT_OF_RANGE, "quarter lies outside the range")
        start_index = (start_year - MIN_YEAR) * 12 + (start_month - 1)
        end_month = Month(start_month + 2)
        end_index = (start_year - MIN_YEAR) * 12 + (end_month - 1)
        end_day = MONTH_LENGTHS[end_index]
        return DateRange(
            _from_parts(start_year, start_month, 1, MONTH_START_ORD[start_index]),
            _from_parts(start_year, end_month, end_day, MONTH_START_ORD[end_index] + end_day - 1),
        )

    def label(self, lang: Lang = Lang.EN) -> str:
        """The label like ``2082/83``, localised per language.

        Args:
            lang: The language of the digits.

        Returns:
            ``"2082/83"`` for English, ``"२०८२/८३"`` for Nepali.
        """
        if lang is Lang.NE:
            return (
                _YEARS_NE[self._start_year - _MIN_FY]
                + "/"
                + _TWO_DIGIT_NE[(self._start_year + 1) % 100]
            )
        return f"{self._start_year}/{(self._start_year + 1) % 100:02d}"

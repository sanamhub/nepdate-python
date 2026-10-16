"""DateDiff: the calendar breakdown between two dates (ALGORITHM §8a)."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True, slots=True)
class DateDiff:
    """The signed years, months and days between two dates.

    Attributes:
        negative: True when the first date is after the second.
        years: The whole years in the breakdown.
        months: The whole months, 0 through 11, after the years.
        days: The remaining days, 0 through 32.
        total_days: The signed day difference, ``a.days_until(b)``.
    """

    negative: bool
    years: int
    months: int
    days: int
    total_days: int

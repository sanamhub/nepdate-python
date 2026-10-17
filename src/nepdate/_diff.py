"""DateDiff: the calendar breakdown between two dates (ALGORITHM §8a)."""

from __future__ import annotations


class DateDiff:
    """The signed years, months and days between two dates.

    An immutable value: equal breakdowns compare and hash equal. It is written by hand, not with
    ``dataclasses``, because that module pulls 27 more modules into ``import nepdate`` and breaks
    the ADR-0002 §7 import budget.

    Attributes:
        negative: True when the first date is after the second.
        years: The whole years in the breakdown.
        months: The whole months, 0 through 11, after the years.
        days: The remaining days, 0 through 32.
        total_days: The signed day difference, ``a.days_until(b)``.
    """

    __slots__ = ("days", "months", "negative", "total_days", "years")

    negative: bool
    years: int
    months: int
    days: int
    total_days: int

    def __init__(self, negative: bool, years: int, months: int, days: int, total_days: int) -> None:
        """Build a breakdown from its parts.

        Args:
            negative: True when the first date is after the second.
            years: The whole years.
            months: The whole months after the years.
            days: The remaining days.
            total_days: The signed day difference.
        """
        set_field = object.__setattr__
        set_field(self, "negative", negative)
        set_field(self, "years", years)
        set_field(self, "months", months)
        set_field(self, "days", days)
        set_field(self, "total_days", total_days)

    def _key(self) -> tuple[bool, int, int, int, int]:
        return (self.negative, self.years, self.months, self.days, self.total_days)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DateDiff):
            return NotImplemented
        return self._key() == other._key()

    def __hash__(self) -> int:
        return hash(self._key())

    def __repr__(self) -> str:
        return (
            f"DateDiff(negative={self.negative!r}, years={self.years!r}, "
            f"months={self.months!r}, days={self.days!r}, total_days={self.total_days!r})"
        )

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError(f"DateDiff is immutable; cannot set {name!r}")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"DateDiff is immutable; cannot delete {name!r}")

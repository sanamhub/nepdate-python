"""Ordered batch conversion in both directions.

Every function keeps the input order, which is the port contract: the C# parallel path does
not promise an order above 500 items, so a port does not copy it.
"""

from __future__ import annotations

import datetime

from ._date import NepaliDate

# `typing` would add modules to `import nepdate` (the import gate); a module-level constant is
# enough for the type checker, as in `_date.py`.
TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Iterable


def to_nepali_dates(dates: Iterable[datetime.date]) -> list[NepaliDate]:
    """Convert every Gregorian date to a BS date, in input order.

    Args:
        dates: The Gregorian dates, the same ordinals as ``datetime.date``.

    Returns:
        One BS date per input, in the same order.

    Raises:
        NepDateError: An input is outside AD 1844-04-11 through 2143-04-15.
    """
    return [NepaliDate.from_date(d) for d in dates]


def to_english_dates(items: Iterable[NepaliDate | str]) -> list[datetime.date]:
    """Convert every BS date or date string to its Gregorian date, in input order.

    Args:
        items: ``NepaliDate`` values, or strings in the strict form of PARSING §1.

    Returns:
        One Gregorian date per input, in the same order.

    Raises:
        NepDateError: A string is malformed or names an invalid date.
        TypeError: An item is neither a date nor a string.
    """
    result: list[datetime.date] = []
    for item in items:
        if isinstance(item, str):
            result.append(NepaliDate.parse(item).to_date())
        elif isinstance(item, NepaliDate):
            result.append(item.to_date())
        else:
            raise TypeError(f"expected a NepaliDate or a string, not {type(item).__name__}")
    return result

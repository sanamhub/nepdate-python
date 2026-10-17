"""Bikram Sambat (Nepali calendar) for Python.

The public surface is ``nepdate.__all__``, documented in ``docs/API.md``. The core package
is dependency-free (except ``tzdata`` on Windows, for ``today()``) and contains none of the
tithi, holiday or event data; that lives in the separate ``nepdate-patro`` distribution
(``nepdate_patro``).
"""

from ._date import MAX, MIN, NepaliDate
from ._diff import DateDiff
from ._errors import ErrorKind, NepDateError
from ._fiscal import FiscalYear
from ._names import (
    DateOrder,
    Lang,
    Month,
    Overflow,
    Quarter,
    Separator,
    Weekday,
    to_nepali_digits,
)
from ._range import DateRange

__all__ = [
    "MAX",
    "MIN",
    "DateDiff",
    "DateOrder",
    "DateRange",
    "ErrorKind",
    "FiscalYear",
    "Lang",
    "Month",
    "NepDateError",
    "NepaliDate",
    "Overflow",
    "Quarter",
    "Separator",
    "Weekday",
    "to_nepali_digits",
]

"""Bikram Sambat (Nepali calendar) for Python.

The public surface is ``nepdate.__all__``, documented in ``docs/API.md``. The core package
is dependency-free (except ``tzdata`` on Windows, for ``today()``) and contains none of the
tithi, holiday or event data; that lives in the separate ``nepdate-patro`` distribution
(``nepdate_patro``).
"""

from ._date import MAX, MIN, NepaliDate
from ._errors import ErrorKind, NepDateError
from ._names import Lang, Month, Weekday

__all__ = [
    "MAX",
    "MIN",
    "ErrorKind",
    "Lang",
    "Month",
    "NepDateError",
    "NepaliDate",
    "Weekday",
]

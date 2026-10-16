"""Error kinds and the one exception type the package raises."""

from __future__ import annotations

import enum


class ErrorKind(enum.Enum):
    """Which validation rule a ``NepDateError`` failed, for programmatic matching."""

    OUT_OF_RANGE = "out_of_range"
    INVALID_MONTH = "invalid_month"
    INVALID_DAY = "invalid_day"
    INVALID_GREGORIAN = "invalid_gregorian"
    INVALID_CHARACTER = "invalid_character"
    WRONG_GROUP_COUNT = "wrong_group_count"
    NUMBER_TOO_LONG = "number_too_long"
    AMBIGUOUS = "ambiguous"
    UNRECOGNIZED = "unrecognized"


class NepDateError(ValueError):
    """Raised for every invalid date; ``kind`` names the failed rule.

    Subclasses ``ValueError`` so ``except ValueError`` keeps working, as with
    ``datetime.date``.
    """

    __slots__ = ("_kind",)

    def __init__(self, kind: ErrorKind, message: str) -> None:
        super().__init__(message)
        self._kind = kind

    @property
    def kind(self) -> ErrorKind:
        """The ``ErrorKind`` of this error, for ``is`` comparison."""
        return self._kind

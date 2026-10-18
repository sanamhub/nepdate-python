"""The strict and lenient parsers of PARSING §1-2: hand-written scanners, no ``re``."""

from __future__ import annotations

from ._errors import ErrorKind, NepDateError

# `typing` would add modules to `import nepdate` (the import gate); a module-level constant is
# enough for the type checker, as in `_date.py`.
TYPE_CHECKING = False
if TYPE_CHECKING:
    from ._date import NepaliDate

_GROUP_COUNT = 3
_MAX_DIGITS = 4
_ASCII_ZERO = 0x30
_ASCII_NINE = 0x39
_DEVA_ZERO = 0x0966
_DEVA_NINE = 0x096F
_SEPARATORS = "-/._\\ ।|"


def parse_strict(s: str, date_type: type[NepaliDate]) -> NepaliDate:
    """Parse the strict form of PARSING §1.

    Args:
        s: The text, year then month then day in ASCII or Devanagari digits.
        date_type: The ``NepaliDate`` class, passed to avoid a circular import.

    Returns:
        The parsed date.

    Raises:
        NepDateError: The text is malformed or names an invalid date.
    """
    fast = _fast_parse(s, date_type)
    if fast is not None:
        return fast
    return _scan_strict(s, date_type)


def _fast_parse(s: str, date_type: type[NepaliDate]) -> NepaliDate | None:
    """Parse the ASCII fast path of ADR-0002 §5, or return None to let the scanner decide.

    Args:
        s: The input text.
        date_type: The ``NepaliDate`` class.

    Returns:
        The parsed date, or None when the text is not three ASCII digit groups on one separator
        or names an invalid date.
    """
    if not s.isascii():
        return None
    groups = s.split("/")
    if len(groups) != _GROUP_COUNT:
        groups = s.split("-")
        if len(groups) != _GROUP_COUNT:
            return None
    for group in groups:
        if not group or len(group) > _MAX_DIGITS or not group.isdigit():
            return None
    try:
        return date_type(int(groups[0]), int(groups[1]), int(groups[2]))
    except NepDateError:
        return None


def _digit_value(char: str) -> int:
    """Return the value of an ASCII or Devanagari digit, or -1 for any other character."""
    code = ord(char)
    if _ASCII_ZERO <= code <= _ASCII_NINE:
        return code - _ASCII_ZERO
    if _DEVA_ZERO <= code <= _DEVA_NINE:
        return code - _DEVA_ZERO
    return -1


def _scan_strict(s: str, date_type: type[NepaliDate]) -> NepaliDate:
    """Scan the strict form left to right and build the date.

    Args:
        s: The input text.
        date_type: The ``NepaliDate`` class.

    Returns:
        The parsed date.

    Raises:
        NepDateError: The text is malformed or names an invalid date.
    """
    groups = [0, 0, 0]
    count = 0
    in_group = False
    digits = 0
    for char in s:
        value = _digit_value(char)
        if value >= 0:
            if not in_group:
                if count == _GROUP_COUNT:
                    raise NepDateError(ErrorKind.WRONG_GROUP_COUNT, "more than three groups")
                count += 1
                in_group = True
                digits = 0
            digits += 1
            if digits > _MAX_DIGITS:
                raise NepDateError(ErrorKind.NUMBER_TOO_LONG, "a group has more than 4 digits")
            groups[count - 1] = groups[count - 1] * 10 + value
        elif char in _SEPARATORS:
            in_group = False
        else:
            raise NepDateError(ErrorKind.INVALID_CHARACTER, f"invalid character {char!r}")
    if count < _GROUP_COUNT:
        raise NepDateError(ErrorKind.WRONG_GROUP_COUNT, "fewer than three groups")
    return date_type(groups[0], groups[1], groups[2])


def parse_lenient(s: str, date_type: type[NepaliDate]) -> NepaliDate:
    """Parse the lenient form of PARSING §2.

    The lenient tables are imported on the first call, so ``import nepdate`` does not pay for
    them (ADR-0002 §7).

    Args:
        s: Human-written text, for example ``"15 Shrawan 2080"``.
        date_type: The ``NepaliDate`` class, passed to avoid a circular import.

    Returns:
        The parsed date.

    Raises:
        NepDateError: No rule matches or the date is invalid.
    """
    from ._lenient import parse_lenient as _parse_lenient  # noqa: PLC0415 - see module docstring

    return _parse_lenient(s, date_type)

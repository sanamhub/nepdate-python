"""The lenient parser of PARSING §2, loaded on the first ``parse_lenient`` call.

The month-name and fold tables are large enough to matter at import time, so they live in this
module instead of ``_parse``. ``_parse`` imports this module inside ``parse_lenient``; the strict
scanner stays eager because every parse may use it.
"""

from __future__ import annotations

from ._errors import ErrorKind, NepDateError
from ._parse import parse_strict

# `typing` would add modules to `import nepdate` (the import gate); a module-level constant is
# enough for the type checker, as in `_date.py`.
TYPE_CHECKING = False
if TYPE_CHECKING:
    from ._date import NepaliDate

_LENIENT_SEPARATORS = "-/\\_ |।,"
_MAX_DIGITS = 4
_DEVA_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_FOLD = str.maketrans(
    {**{ord(char): ord(char) + 32 for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}, 0x212A: ord("k")}
)
_ERA_MARKERS = (
    "bs",
    "b.s.",
    "b.s",
    "vs",
    "v.s.",
    "v.s",
    "बि.सं.",
    "वि.सं.",
    "बि.सं",
    "वि.सं",
)
_IGNORED_WORDS = ("गते", "मिति")
_MONTH_WORDS = (
    ("baishakh", 1),
    ("baisakh", 1),
    ("baishak", 1),
    ("vaishakh", 1),
    ("vaisakh", 1),
    ("bai", 1),
    ("बैशाख", 1),
    ("वैशाख", 1),
    ("बैसाख", 1),
    ("jestha", 2),
    ("jeth", 2),
    ("jyestha", 2),
    ("jes", 2),
    ("जेठ", 2),
    ("जेष्ठ", 2),
    ("ज्येष्ठ", 2),
    ("ashad", 3),
    ("ashadh", 3),
    ("asar", 3),
    ("asadh", 3),
    ("asa", 3),
    ("असार", 3),
    ("आषाढ", 3),
    ("असाढ", 3),
    ("shrawan", 4),
    ("shravan", 4),
    ("srawan", 4),
    ("sawan", 4),
    ("saun", 4),
    ("shr", 4),
    ("साउन", 4),
    ("श्रावण", 4),
    ("सावन", 4),
    ("bhadra", 5),
    ("bhadau", 5),
    ("bha", 5),
    ("भदौ", 5),
    ("भाद्र", 5),
    ("भाद्रपद", 5),
    ("ashoj", 6),
    ("asoj", 6),
    ("ashwin", 6),
    ("aso", 6),
    ("असोज", 6),
    ("आश्विन", 6),
    ("असौज", 6),
    ("kartik", 7),
    ("kattik", 7),
    ("kar", 7),
    ("कार्तिक", 7),
    ("कात्तिक", 7),
    ("mangsir", 8),
    ("mansir", 8),
    ("margashirsha", 8),
    ("man", 8),
    ("मंसिर", 8),
    ("मङ्सिर", 8),
    ("मार्गशीर्ष", 8),
    ("poush", 9),
    ("paush", 9),
    ("push", 9),
    ("pus", 9),
    ("pou", 9),
    ("पुष", 9),
    ("पौष", 9),
    ("पुस", 9),
    ("magh", 10),
    ("mag", 10),
    ("माघ", 10),
    ("falgun", 11),
    ("phalgun", 11),
    ("fagun", 11),
    ("fal", 11),
    ("फागुन", 11),
    ("फाल्गुन", 11),
    ("chaitra", 12),
    ("chait", 12),
    ("cha", 12),
    ("चैत", 12),
    ("चैत्र", 12),
)
_LENIENT_NUMBERS = 3
_MONTH_NAME_NUMBERS = 2
_MAX_DAY_DIGITS = 2


def parse_lenient(s: str, date_type: type[NepaliDate]) -> NepaliDate:
    """Parse the lenient form of PARSING §2.

    Input is matched as given, with no NFC step and no joiner removal (PARSING §2), so every
    port accepts and rejects the same text.

    Args:
        s: Human-written text, for example ``"15 Shrawan 2080"``.
        date_type: The ``NepaliDate`` class, passed to avoid a circular import.

    Returns:
        The parsed date.

    Raises:
        NepDateError: No rule matches or the date is invalid.
    """
    try:
        strict = parse_strict(s, date_type)
    except NepDateError:
        strict = None
    if strict is not None:
        return strict

    normalized = s.translate(_DEVA_DIGITS)
    numbers, digit_counts, months, unknown = _lenient_tokens(normalized)
    if unknown:
        raise NepDateError(ErrorKind.UNRECOGNIZED, "unknown word")
    if len(months) >= _MONTH_NAME_NUMBERS:
        raise NepDateError(ErrorKind.UNRECOGNIZED, "more than one month name")
    if len(months) == 1 and len(numbers) == _MONTH_NAME_NUMBERS:
        return _month_form(date_type, months[0], numbers, digit_counts)
    if not months and len(numbers) == _LENIENT_NUMBERS:
        return _numeric_form(date_type, numbers, digit_counts)
    raise NepDateError(ErrorKind.UNRECOGNIZED, "unrecognized token count")


def _lenient_tokens(s: str) -> tuple[list[int], list[int], list[int], bool]:
    """Split normalised text into number and month tokens (PARSING §2 step 2).

    Args:
        s: The text after the Devanagari digit mapping.

    Returns:
        The numbers, their digit counts, the month numbers and whether an unknown word appeared.

    Raises:
        NepDateError: A numeric token has more than four digits.
    """
    numbers: list[int] = []
    digit_counts: list[int] = []
    months: list[int] = []
    unknown = False
    index = 0
    length = len(s)
    while index < length:
        if s[index] in _LENIENT_SEPARATORS:
            index += 1
            continue
        end = index
        while end < length and s[end] not in _LENIENT_SEPARATORS:
            end += 1
        chunk = s[index:end]
        index = end
        if _is_numeric(chunk):
            start = 0
            for position in range(len(chunk) + 1):
                if position == len(chunk) or chunk[position] == ".":
                    part = chunk[start:position]
                    if part:
                        if len(part) > _MAX_DIGITS:
                            raise NepDateError(
                                ErrorKind.NUMBER_TOO_LONG, "a number has more than 4 digits"
                            )
                        numbers.append(int(part))
                        digit_counts.append(len(part))
                    start = position + 1
            continue
        value = _word_value(chunk)
        if value > 0:
            months.append(value)
        elif value < 0:
            unknown = True
    return numbers, digit_counts, months, unknown


def _is_numeric(chunk: str) -> bool:
    """Return whether ``chunk`` consists only of ASCII digits and dots."""
    return all("0" <= char <= "9" or char == "." for char in chunk)


def _word_value(token: str) -> int:
    """Return a month number, 0 for a dropped word, or -1 for an unknown word."""
    folded = token.translate(_FOLD)
    for name, month in _MONTH_WORDS:
        if folded == name:
            return month
    if folded in _ERA_MARKERS or folded in _IGNORED_WORDS:
        return 0
    return -1


def _month_form(
    date_type: type[NepaliDate], month: int, numbers: list[int], digit_counts: list[int]
) -> NepaliDate:
    """Apply PARSING §2 step 3 to one month name and two numbers."""
    four = [index for index, count in enumerate(digit_counts) if count == _MAX_DIGITS]
    if len(four) != 1:
        raise NepDateError(ErrorKind.AMBIGUOUS, "no single four-digit year")
    year_index = four[0]
    other_index = 1 - year_index
    if digit_counts[other_index] > _MAX_DAY_DIGITS:
        raise NepDateError(ErrorKind.AMBIGUOUS, "the day has more than two digits")
    return date_type(numbers[year_index], month, numbers[other_index])


def _numeric_form(
    date_type: type[NepaliDate], numbers: list[int], digit_counts: list[int]
) -> NepaliDate:
    """Apply PARSING §2 step 4 to three numbers."""
    if digit_counts[0] == _MAX_DIGITS:
        year, month, day = numbers
    elif digit_counts[2] == _MAX_DIGITS:
        day, month, year = numbers
    else:
        raise NepDateError(ErrorKind.AMBIGUOUS, "no four-digit year first or last")
    return date_type(year, month, day)

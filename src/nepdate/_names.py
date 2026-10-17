"""Calendar enums, their names and the digit table (FORMATTING §1)."""

from __future__ import annotations

import enum

# Index 0 is the empty string so a month or weekday number indexes its name directly.
_MONTH_EN = (
    "",
    "Baishakh",
    "Jestha",
    "Ashad",
    "Shrawan",
    "Bhadra",
    "Ashoj",
    "Kartik",
    "Mangsir",
    "Poush",
    "Magh",
    "Falgun",
    "Chaitra",
)
_MONTH_NE = (
    "",
    "बैशाख",
    "जेठ",
    "असार",
    "साउन",
    "भदौ",
    "असोज",
    "कार्तिक",
    "मंसिर",
    "पुष",
    "माघ",
    "फागुन",
    "चैत",
)
# D-04: Ashad and Ashoj use Asa and Aso instead of the C# "Ash" for both.
_MONTH_EN_SHORT = (
    "",
    "Bai",
    "Jes",
    "Asa",
    "Shr",
    "Bha",
    "Aso",
    "Kar",
    "Man",
    "Pou",
    "Mag",
    "Fal",
    "Cha",
)
_WEEKDAY_EN = (
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
)
_WEEKDAY_EN_SHORT = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")
_WEEKDAY_NE = (
    "आइतवार",
    "सोमवार",
    "मङ्गलवार",
    "बुधवार",
    "बिहिवार",
    "शुक्रवार",
    "शनिवार",
)
_WEEKDAY_NE_SHORT = ("आइत", "सोम", "मङ्गल", "बुध", "बिहि", "शुक्र", "शनि")
_NEPALI_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")


def to_nepali_digits(n: int, min_width: int = 0) -> str:
    """Format ``n`` in ASCII, zero-pad it to ``min_width``, then map the digits to Devanagari.

    Args:
        n: The integer to format.
        min_width: The minimum number of ASCII digits before translation.

    Returns:
        The Devanagari digit string, for example ``"२०८१"`` for ``2081``.
    """
    return f"{n:0{min_width}d}".translate(_NEPALI_DIGITS)


class Lang(enum.Enum):
    """Output language: ``EN`` is ASCII, ``NE`` is Nepali (Devanagari)."""

    EN = "en"
    NE = "ne"


class Month(enum.IntEnum):
    """A Bikram Sambat month, 1 = Baishakh through 12 = Chaitra."""

    BAISHAKH = 1
    JESTHA = 2
    ASHAD = 3
    SHRAWAN = 4
    BHADRA = 5
    ASHOJ = 6
    KARTIK = 7
    MANGSIR = 8
    POUSH = 9
    MAGH = 10
    FALGUN = 11
    CHAITRA = 12

    def label(self, lang: Lang = Lang.EN) -> str:
        """The full month name in ``lang``, for example ``"Shrawan"`` or ``"साउन"``."""
        if lang is Lang.NE:
            return _MONTH_NE[self.value]
        return _MONTH_EN[self.value]

    def short_label(self, lang: Lang = Lang.EN) -> str:
        """The short month name in ``lang``; Nepali has no abbreviation (FORMATTING §1)."""
        if lang is Lang.NE:
            return _MONTH_NE[self.value]
        return _MONTH_EN_SHORT[self.value]


class Weekday(enum.IntEnum):
    """A weekday with Sunday = 0, the spec's numbering (not datetime's Monday = 0)."""

    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6

    def label(self, lang: Lang = Lang.EN) -> str:
        """The full weekday name in ``lang``, for example ``"Tuesday"`` or ``"मङ्गलवार"``."""
        if lang is Lang.NE:
            return _WEEKDAY_NE[self.value]
        return _WEEKDAY_EN[self.value]

    def short_label(self, lang: Lang = Lang.EN) -> str:
        """The short weekday name in ``lang``, for example ``"Tue"`` or ``"मङ्गल"``."""
        if lang is Lang.NE:
            return _WEEKDAY_NE_SHORT[self.value]
        return _WEEKDAY_EN_SHORT[self.value]


class Overflow(enum.Enum):
    """How ``add_months`` and ``add_years`` handle a day past the month end."""

    CLAMP = "clamp"
    SPILL = "spill"


class Quarter(enum.IntEnum):
    """A fiscal quarter: Q1 = Shrawan..Ashoj through Q4 = Baishakh..Ashad."""

    Q1 = 1
    Q2 = 2
    Q3 = 3
    Q4 = 4

    def months(self) -> tuple[Month, Month, Month]:
        """The three BS months of this quarter, in calendar order."""
        first = ((self.value - 1) * 3 + 4 - 1) % 12 + 1
        return (Month(first), Month(first % 12 + 1), Month((first + 1) % 12 + 1))

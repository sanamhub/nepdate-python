"""Calendar enums: language, month and weekday."""

from __future__ import annotations

import enum


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


class Weekday(enum.IntEnum):
    """A weekday with Sunday = 0, the spec's numbering (not datetime's Monday = 0)."""

    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6


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

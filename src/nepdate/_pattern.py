"""The hand-written pattern formatter of FORMATTING §5: one left-to-right pass, no ``re``.

The plan's ``functools.lru_cache`` is not used: ``functools`` is outside ``CORE_IMPORT_ALLOWED``
and a module-level cache would be mutable state (AGENTS.md §2). The scanner runs once per call.
"""

from __future__ import annotations

from ._calendar import MIN_YEAR
from ._format import (
    _DAY_EN,
    _DAY_EN_PAD,
    _DAY_NE,
    _DAY_NE_PAD,
    _YEAR2_EN,
    _YEAR2_NE,
    _YEAR_EN,
    _YEAR_NE,
    format_default,
    format_iso,
    format_long,
)
from ._names import _MONTH_EN, _MONTH_EN_SHORT, _MONTH_NE, Lang

_FULL_YEAR_RUN = 4
_SHORT_MONTH_RUN = 3
_PADDED_DAY_RUN = 2
_STANDARD_DEFAULT = ("", "G", "g", "d")


def format_pattern(  # noqa: PLR0912, PLR0915 - one-pass scanner by design
    pattern: str,
    year: int,
    month: int,
    day: int,
    lang: Lang,
) -> str:
    """Format a date with a standard or custom pattern (FORMATTING §5).

    Args:
        pattern: The standard pattern or the custom pattern.
        year: The BS year.
        month: The BS month.
        day: The BS day.
        lang: The language of the names and digits.

    Returns:
        The formatted date; literal characters are never localised.
    """
    if pattern in _STANDARD_DEFAULT:
        return format_default(year, month, day, lang)
    if pattern == "D":
        return format_long(
            year,
            month,
            day,
            None,
            include_year=True,
            pad=True,
            lang=lang,
        )
    if pattern == "s":
        return format_iso(year, month, day, lang)

    if lang is Lang.NE:
        year_text = _YEAR_NE[year - MIN_YEAR]
        year2_text = _YEAR2_NE[year % 100]
        month_name = _MONTH_NE[month]
        month_short = _MONTH_NE[month]
        month_pad = _DAY_NE_PAD[month]
        month_plain = _DAY_NE[month]
        day_pad = _DAY_NE_PAD[day]
        day_plain = _DAY_NE[day]
    else:
        year_text = _YEAR_EN[year - MIN_YEAR]
        year2_text = _YEAR2_EN[year % 100]
        month_name = _MONTH_EN[month]
        month_short = _MONTH_EN_SHORT[month]
        month_pad = _DAY_EN_PAD[month]
        month_plain = _DAY_EN[month]
        day_pad = _DAY_EN_PAD[day]
        day_plain = _DAY_EN[day]

    out: list[str] = []
    append = out.append
    index = 0
    length = len(pattern)
    while index < length:
        char = pattern[index]
        if char == "\\":
            if index + 1 < length:
                append(pattern[index + 1])
            index += 2
            continue
        if char == "'":
            end = pattern.find("'", index + 1)
            if end < 0:
                append(pattern[index + 1 :])
                break
            append(pattern[index + 1 : end])
            index = end + 1
            continue
        if char == "y":
            end = index + 1
            while end < length and pattern[end] == "y":
                end += 1
            append(year_text if end - index >= _FULL_YEAR_RUN else year2_text)
            index = end
            continue
        if char == "M":
            end = index + 1
            while end < length and pattern[end] == "M":
                end += 1
            run = end - index
            if run >= _FULL_YEAR_RUN:
                append(month_name)
            elif run == _SHORT_MONTH_RUN:
                append(month_short)
            elif run == _PADDED_DAY_RUN:
                append(month_pad)
            else:
                append(month_plain)
            index = end
            continue
        if char == "d":
            end = index + 1
            while end < length and pattern[end] == "d":
                end += 1
            append(day_pad if end - index == _PADDED_DAY_RUN else day_plain)
            index = end
            continue
        append(char)
        index += 1
    return "".join(out)

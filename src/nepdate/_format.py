"""Formatting for NepaliDate: the tables of FORMATTING §1-4 and one f-string per format."""

from __future__ import annotations

from ._calendar import MAX_YEAR, MIN_YEAR
from ._names import (
    _MONTH_EN,
    _MONTH_NE,
    _WEEKDAY_EN,
    _WEEKDAY_NE,
    DateOrder,
    Lang,
    Separator,
)

_NEPALI_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")
_DAY_EN_PAD = tuple(f"{day:02d}" for day in range(33))
_DAY_EN = tuple(str(day) for day in range(33))
_DAY_NE_PAD = tuple(day.translate(_NEPALI_DIGITS) for day in _DAY_EN_PAD)
_DAY_NE = tuple(day.translate(_NEPALI_DIGITS) for day in _DAY_EN)
_YEAR_EN = tuple(str(year) for year in range(MIN_YEAR, MAX_YEAR + 1))
_YEAR_NE = tuple(year.translate(_NEPALI_DIGITS) for year in _YEAR_EN)
_YEAR2_EN = tuple(f"{year:02d}" for year in range(100))
_YEAR2_NE = tuple(year.translate(_NEPALI_DIGITS) for year in _YEAR2_EN)


def format_default(year: int, month: int, day: int, lang: Lang) -> str:
    """Format ``YYYY/MM/DD`` with the digits of ``lang`` (FORMATTING §2).

    Args:
        year: The BS year.
        month: The BS month.
        day: The BS day.
        lang: The language of the digits.

    Returns:
        The default display, for example ``"2081/04/15"``.
    """
    if lang is Lang.NE:
        return f"{_YEAR_NE[year - MIN_YEAR]}/{_DAY_NE_PAD[month]}/{_DAY_NE_PAD[day]}"
    return f"{_YEAR_EN[year - MIN_YEAR]}/{_DAY_EN_PAD[month]}/{_DAY_EN_PAD[day]}"


def format_iso(year: int, month: int, day: int, lang: Lang) -> str:
    """Format ``YYYY-MM-DD`` with the digits of ``lang`` (D-11).

    Args:
        year: The BS year.
        month: The BS month.
        day: The BS day.
        lang: The language of the digits.

    Returns:
        The sortable form, for example ``"2081-04-15"``.
    """
    if lang is Lang.NE:
        return f"{_YEAR_NE[year - MIN_YEAR]}-{_DAY_NE_PAD[month]}-{_DAY_NE_PAD[day]}"
    return f"{_YEAR_EN[year - MIN_YEAR]}-{_DAY_EN_PAD[month]}-{_DAY_EN_PAD[day]}"


def format_short(  # noqa: PLR0913, PLR0917 - the three date fields are separate on purpose
    year: int,
    month: int,
    day: int,
    order: DateOrder,
    separator: Separator,
    pad: bool,
    lang: Lang,
) -> str:
    """Format the short form of FORMATTING §3.

    Args:
        year: The BS year.
        month: The BS month.
        day: The BS day.
        order: The field order.
        separator: The separator between fields.
        pad: Whether month and day are two digits.
        lang: The language of the digits.

    Returns:
        The short form, for example ``"2080-05-15"``.

    Raises:
        ValueError: ``order`` is not a ``DateOrder``.
    """
    if lang is Lang.NE:
        y = _YEAR_NE[year - MIN_YEAR]
        m = _DAY_NE_PAD[month] if pad else _DAY_NE[month]
        d = _DAY_NE_PAD[day] if pad else _DAY_NE[day]
    else:
        y = _YEAR_EN[year - MIN_YEAR]
        m = _DAY_EN_PAD[month] if pad else _DAY_EN[month]
        d = _DAY_EN_PAD[day] if pad else _DAY_EN[day]
    sep = separator.value
    if order is DateOrder.YMD:
        return f"{y}{sep}{m}{sep}{d}"
    if order is DateOrder.YDM:
        return f"{y}{sep}{d}{sep}{m}"
    if order is DateOrder.MYD:
        return f"{m}{sep}{y}{sep}{d}"
    if order is DateOrder.MDY:
        return f"{m}{sep}{d}{sep}{y}"
    if order is DateOrder.DYM:
        return f"{d}{sep}{y}{sep}{m}"
    if order is DateOrder.DMY:
        return f"{d}{sep}{m}{sep}{y}"
    raise ValueError(f"unknown date order: {order!r}")


def format_long(  # noqa: PLR0913 - the three date fields and the four options are explicit
    year: int,
    month: int,
    day: int,
    weekday: int,
    *,
    with_weekday: bool,
    include_year: bool,
    pad: bool,
    lang: Lang,
) -> str:
    """Format the long form of FORMATTING §4.

    Args:
        year: The BS year.
        month: The BS month.
        day: The BS day.
        weekday: The weekday index, Sunday = 0.
        with_weekday: Whether to start with the weekday name.
        include_year: Whether to end with the year.
        pad: Whether the day is two digits.
        lang: The language of the names and digits.

    Returns:
        The long form, for example ``"Tuesday, Shrawan 15, 2081"``.
    """
    if lang is Lang.NE:
        y = _YEAR_NE[year - MIN_YEAR]
        d = _DAY_NE_PAD[day] if pad else _DAY_NE[day]
        month_name = _MONTH_NE[month]
        prefix = f"{_WEEKDAY_NE[weekday]}, " if with_weekday else ""
    else:
        y = _YEAR_EN[year - MIN_YEAR]
        d = _DAY_EN_PAD[day] if pad else _DAY_EN[day]
        month_name = _MONTH_EN[month]
        prefix = f"{_WEEKDAY_EN[weekday]}, " if with_weekday else ""
    suffix = f", {y}" if include_year else ""
    return f"{prefix}{month_name} {d}{suffix}"

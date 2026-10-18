"""Hypothesis properties for parsing and formatting, each against an independent oracle (P9-01)."""

from __future__ import annotations

import datetime
from collections.abc import Callable

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nepdate import Lang, NepaliDate, Overflow, _calendar
from nepdate._errors import ErrorKind, NepDateError

_OFFSET = _calendar.ORDINAL_OFFSET
_MAX_SERIAL = _calendar.MONTH_START[-1] - 1
_TOTAL_MONTHS = len(_calendar.MONTH_LENGTHS)
_MONTHS_PER_YEAR = 12
_CHAITRA = 12
_AD_MIN = datetime.date(1844, 4, 11)
_AD_MAX = datetime.date(2143, 4, 15)
_ASCII_DIGITS = "0123456789"
_DEVANAGARI_DIGITS = "०१२३४५६७८९"
_TO_DEVANAGARI = str.maketrans(_ASCII_DIGITS, _DEVANAGARI_DIGITS)

_Parser = Callable[[str], NepaliDate]
_Case = tuple[str, Lang, _Parser]

# Standard patterns and the custom forms that produce a full year in a parseable order. The
# expected result is the generated date, not another call to the formatter.
_FORMAT_CASES: tuple[_Case, ...] = (
    ("", Lang.EN, NepaliDate.parse),
    ("G", Lang.EN, NepaliDate.parse),
    ("g", Lang.EN, NepaliDate.parse),
    ("d", Lang.EN, NepaliDate.parse),
    ("s", Lang.EN, NepaliDate.parse),
    ("D", Lang.EN, NepaliDate.parse_lenient),
    ("", Lang.NE, NepaliDate.parse),
    ("G", Lang.NE, NepaliDate.parse),
    ("g", Lang.NE, NepaliDate.parse),
    ("d", Lang.NE, NepaliDate.parse),
    ("s", Lang.NE, NepaliDate.parse),
    ("D", Lang.NE, NepaliDate.parse_lenient),
    ("yyyy-MM-dd", Lang.EN, NepaliDate.parse),
    ("yyyy/MM/dd", Lang.EN, NepaliDate.parse),
    ("yyyy.MM.dd", Lang.EN, NepaliDate.parse),
    ("yyyy_MM_dd", Lang.EN, NepaliDate.parse),
    ("yyyy MM dd", Lang.EN, NepaliDate.parse),
    ("yyyy-M-d", Lang.EN, NepaliDate.parse),
    ("yyyy/M/d", Lang.EN, NepaliDate.parse),
    ("yyyyy-MM-dd", Lang.EN, NepaliDate.parse),
    ("yyyy\\-MM\\-dd", Lang.EN, NepaliDate.parse),
    ("yyyy'/'MM'/'dd", Lang.EN, NepaliDate.parse),
    ("yyyy-MM-dd", Lang.NE, NepaliDate.parse),
    ("yyyy/MM/dd", Lang.NE, NepaliDate.parse),
    ("dd MMMM yyyy", Lang.EN, NepaliDate.parse_lenient),
    ("MMMM d, yyyy", Lang.EN, NepaliDate.parse_lenient),
    ("yyyy MMMM d", Lang.EN, NepaliDate.parse_lenient),
    ("dd MMM yyyy", Lang.EN, NepaliDate.parse_lenient),
    ("dd MMMM yyyy 'BS'", Lang.EN, NepaliDate.parse_lenient),
    ("dd MMMM yyyy", Lang.NE, NepaliDate.parse_lenient),
    ("MMMM d, yyyy", Lang.NE, NepaliDate.parse_lenient),
    ("dd MMM yyyy", Lang.NE, NepaliDate.parse_lenient),
)


def _date(serial: int) -> NepaliDate:
    """Build a date from a serial number without using a formatter."""
    return NepaliDate.from_ordinal(_OFFSET + serial)


@given(serial=st.integers(0, _MAX_SERIAL), case=st.sampled_from(_FORMAT_CASES))
def test_format_round_trips_through_parse(serial: int, case: _Case) -> None:
    """Every standard and custom pattern that carries a full year parses back to the date."""
    pattern, lang, parser = case
    date = _date(serial)
    assert parser(date.format(pattern, lang)) == date


@given(st.text(max_size=40))
def test_lenient_never_raises_anything_but_nepdate_error(text: str) -> None:
    """Arbitrary text returns a date or raises ``NepDateError``, never another exception."""
    try:
        NepaliDate.parse_lenient(text)
    except NepDateError:
        return


@given(st.text(max_size=40))
def test_lenient_agrees_on_every_strict_valid_text(text: str) -> None:
    """When strict parsing accepts text, lenient parsing returns the same date."""
    try:
        strict = NepaliDate.parse(text)
    except NepDateError:
        return
    assert NepaliDate.parse_lenient(text) == strict


@pytest.mark.parametrize("pattern", ["yyyy-MM-dd", "yyyy/MM/dd"])
@given(serial=st.integers(0, _MAX_SERIAL))
def test_format_digits_match_lang(serial: int, pattern: str) -> None:
    """English output is ASCII and Nepali output is the same text in Devanagari digits."""
    date = _date(serial)
    english = f"{date.year:04d}-{date.month:02d}-{date.day:02d}"
    if pattern == "yyyy/MM/dd":
        english = english.replace("-", "/")
    assert date.format(pattern, Lang.EN) == english
    assert date.format(pattern, Lang.NE) == english.translate(_TO_DEVANAGARI)


@given(st.dates(min_value=_AD_MIN, max_value=_AD_MAX))
def test_ordinals_match_datetime(ad_date: datetime.date) -> None:
    """to_ordinal, to_date and from_ordinal agree with ``datetime.date`` for in-range dates."""
    date = NepaliDate.from_date(ad_date)
    assert date.to_ordinal() == ad_date.toordinal()
    assert date.to_date() == ad_date
    assert NepaliDate.from_ordinal(ad_date.toordinal()) == date


def _oracle_add_months(date: NepaliDate, n: int, overflow: Overflow) -> NepaliDate:
    """Compute add_months from a month index and the month-length table.

    Raises:
        NepDateError: The target month or spill is outside the supported range.
    """
    index = (date.year - _calendar.MIN_YEAR) * _MONTHS_PER_YEAR + date.month - 1 + n
    if index < 0 or index >= _TOTAL_MONTHS:
        raise NepDateError(ErrorKind.OUT_OF_RANGE, "oracle: month outside the range")
    year, month0 = divmod(index, _MONTHS_PER_YEAR)
    year += _calendar.MIN_YEAR
    month = month0 + 1
    length = _calendar.MONTH_LENGTHS[index]
    if date.day <= length:
        return NepaliDate(year, month, date.day)
    if overflow is Overflow.SPILL:
        if month == _CHAITRA:
            year += 1
            month = 1
        else:
            month += 1
        if year > _calendar.MAX_YEAR:
            raise NepDateError(ErrorKind.OUT_OF_RANGE, "oracle: spill outside the range")
        return NepaliDate(year, month, date.day - length)
    return NepaliDate(year, month, length)


@given(
    serial=st.integers(0, _MAX_SERIAL),
    n=st.integers(-_TOTAL_MONTHS, _TOTAL_MONTHS),
    overflow=st.sampled_from((Overflow.CLAMP, Overflow.SPILL)),
)
def test_add_months_matches_month_index_oracle(serial: int, n: int, overflow: Overflow) -> None:
    """CLAMP and SPILL agree with a month-index oracle built from the table."""
    date = _date(serial)
    try:
        expected = _oracle_add_months(date, n, overflow)
    except NepDateError as exc:
        assert exc.kind is ErrorKind.OUT_OF_RANGE
        with pytest.raises(NepDateError) as caught:
            date.add_months(n, overflow)
        assert caught.value.kind is ErrorKind.OUT_OF_RANGE
    else:
        assert date.add_months(n, overflow) == expected


@given(serial=st.integers(0, _MAX_SERIAL))
def test_plain_outputs_round_trip(serial: int) -> None:
    """str, isoformat, short and long without a weekday are parseable back to the date."""
    date = _date(serial)
    assert NepaliDate.parse(str(date)) == date
    assert NepaliDate.parse(date.isoformat()) == date
    assert NepaliDate.parse(date.short()) == date
    assert NepaliDate.parse(date.short(pad=False)) == date
    assert NepaliDate.parse_lenient(date.long()) == date
    assert NepaliDate.parse_lenient(date.long(lang=Lang.NE)) == date


@given(serial=st.integers(0, _MAX_SERIAL))
def test_dunder_format_matches_format(serial: int) -> None:
    """An empty spec is str, and a non-empty spec is format with English."""
    date = _date(serial)
    assert format(date, "") == str(date)
    assert format(date, "s") == date.isoformat()
    assert format(date, "yyyy-MM-dd") == date.format("yyyy-MM-dd", Lang.EN)

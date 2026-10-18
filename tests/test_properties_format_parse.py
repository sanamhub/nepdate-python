"""Hypothesis properties for parsing and formatting, each against an independent oracle (P9-01)."""

from __future__ import annotations

import datetime
import json
from collections.abc import Callable
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nepdate import Lang, NepaliDate, Overflow
from nepdate._errors import ErrorKind, NepDateError

# The oracles read the hub data file, not the package's generated `_calendar` table, so a
# wrong table in the package cannot agree with itself.
_HUB = json.loads(
    (
        Path(__file__).resolve().parents[1] / "shared" / "data" / "calendar" / "bs-calendar.json"
    ).read_text(encoding="utf-8")
)
_MIN_YEAR: int = _HUB["min_year"]
_MAX_YEAR: int = _HUB["max_year"]
_MONTH_LENGTHS: tuple[int, ...] = tuple(
    length
    for year in range(_MIN_YEAR, _MAX_YEAR + 1)
    for length in _HUB["month_lengths"][str(year)]
)
_OFFSET = datetime.date.fromisoformat(_HUB["epoch"]["ad"]).toordinal()
_MAX_SERIAL = sum(_MONTH_LENGTHS) - 1
_TOTAL_MONTHS = len(_MONTH_LENGTHS)
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
def test_lenient_returns_the_strict_result_when_strict_accepts(text: str) -> None:
    """PARSING §2 step 1: lenient returns the strict result first.

    ``parse_lenient`` calls ``parse_strict`` before its own scanner, so this guards that
    delegation only; it cannot see a divergence in the lenient scanner. The independent check
    is ``test_lenient_numeric_forms_match_the_hub_date``.
    """
    try:
        strict = NepaliDate.parse(text)
    except NepDateError:
        return
    assert NepaliDate.parse_lenient(text) == strict


def _hub_ymd(serial: int) -> tuple[int, int, int]:
    """Return the BS year, month and day of a day serial from the hub month lengths."""
    remaining = serial
    for index, length in enumerate(_MONTH_LENGTHS):
        if remaining < length:
            year, month0 = divmod(index, _MONTHS_PER_YEAR)
            return _MIN_YEAR + year, month0 + 1, remaining + 1
        remaining -= length
    raise AssertionError(f"serial {serial} is past the hub data")


_LENIENT_GAPS = st.text(alphabet=" -/_|।,\\", min_size=1, max_size=3)
_LENIENT_EXTRAS = st.sampled_from(("", "BS", "b.s.", "V.S", "वि.सं.", "गते", "मिति"))


@st.composite
def _lenient_numeric(draw: st.DrawFn) -> tuple[str, tuple[int, int, int]]:
    """Render a hub date as a numeric lenient input the strict parser rejects."""
    ymd = _hub_ymd(draw(st.integers(0, _MAX_SERIAL)))
    year, month, day = ymd
    tokens = [
        f"{year:04d}",
        f"{month:0{draw(st.integers(1, 2))}d}",
        f"{day:0{draw(st.integers(1, 2))}d}",
    ]
    tokens = [token.translate(_TO_DEVANAGARI) if draw(st.booleans()) else token for token in tokens]
    if draw(st.booleans()):
        tokens.reverse()
    extra = draw(_LENIENT_EXTRAS)
    if extra:
        tokens.insert(draw(st.integers(0, len(tokens))), extra)
    # A comma is a lenient-only separator, so every input skips the strict path.
    text = tokens[0] + "," + draw(_LENIENT_GAPS)
    for token in tokens[1:]:
        text += token + draw(_LENIENT_GAPS)
    return draw(st.sampled_from(("", " ", "  "))) + text.rstrip(), ymd


@given(case=_lenient_numeric())
def test_lenient_numeric_forms_match_the_hub_date(case: tuple[str, tuple[int, int, int]]) -> None:
    """Numeric lenient input parses to the date computed from the hub data.

    Covers Y M D and D M Y with mixed digit scripts, separators, era markers and ignored words,
    all on inputs the strict parser rejects.
    """
    text, (year, month, day) = case
    with pytest.raises(NepDateError):
        NepaliDate.parse(text)
    parsed = NepaliDate.parse_lenient(text)
    assert (parsed.year, parsed.month, parsed.day) == (year, month, day)


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
    """Compute add_months from a month index and the hub month lengths.

    Raises:
        NepDateError: The target month or spill is outside the supported range.
    """
    index = (date.year - _MIN_YEAR) * _MONTHS_PER_YEAR + date.month - 1 + n
    if index < 0 or index >= _TOTAL_MONTHS:
        raise NepDateError(ErrorKind.OUT_OF_RANGE, "oracle: month outside the range")
    year, month0 = divmod(index, _MONTHS_PER_YEAR)
    year += _MIN_YEAR
    month = month0 + 1
    length = _MONTH_LENGTHS[index]
    if date.day <= length:
        return NepaliDate(year, month, date.day)
    if overflow is Overflow.SPILL:
        if month == _CHAITRA:
            year += 1
            month = 1
        else:
            month += 1
        if year > _MAX_YEAR:
            raise NepDateError(ErrorKind.OUT_OF_RANGE, "oracle: spill outside the range")
        return NepaliDate(year, month, date.day - length)
    return NepaliDate(year, month, length)


@given(
    serial=st.integers(0, _MAX_SERIAL),
    n=st.integers(-_TOTAL_MONTHS, _TOTAL_MONTHS),
    overflow=st.sampled_from((Overflow.CLAMP, Overflow.SPILL)),
)
def test_add_months_matches_month_index_oracle(serial: int, n: int, overflow: Overflow) -> None:
    """CLAMP and SPILL agree with a month-index oracle built from the hub data."""
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

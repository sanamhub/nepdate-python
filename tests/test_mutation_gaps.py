"""Regression tests for mutation-testing survivors (P8-03)."""

from __future__ import annotations

import datetime
import operator
from collections.abc import Callable

import pytest

from nepdate import DateRange, FiscalYear, Lang, NepaliDate, Overflow, Quarter
from nepdate._calendar import MONTH_NUM, MONTH_START_ORD, MONTH_YEAR
from nepdate._date import _from_serial, _now
from nepdate._errors import ErrorKind, NepDateError


def test_first_of_month_keeps_the_year_month_and_day() -> None:
    """first_of_month returns day 1 with the same year and month."""
    first = NepaliDate(2080, 5, 15).first_of_month()
    assert (first.year, first.month, first.day) == (2080, 5, 1)


def test_last_of_month_keeps_the_year_month_and_day() -> None:
    """last_of_month returns the month length with the same year and month."""
    last = NepaliDate(2080, 5, 15).last_of_month()
    assert (last.year, last.month, last.day) == (2080, 5, 31)


def test_add_months_keeps_the_fields_on_a_plain_result() -> None:
    """A plain month shift keeps the requested year, month and day."""
    result = NepaliDate(2080, 5, 15).add_months(1)
    assert (result.year, result.month, result.day) == (2080, 6, 15)


def test_add_months_keeps_the_fields_when_it_clamps() -> None:
    """A clamped result keeps the target year and month and the last valid day."""
    result = NepaliDate(2081, 4, 32).add_months(2)
    assert (result.year, result.month, result.day) == (2081, 6, 30)


def test_add_months_keeps_the_fields_when_it_spills() -> None:
    """A spilled result carries the overflow day into the next month."""
    result = NepaliDate(2081, 4, 32).add_months(2, Overflow.SPILL)
    assert (result.year, result.month, result.day) == (2081, 7, 2)


def test_add_years_keeps_the_fields_when_it_spills() -> None:
    """add_years forwards the overflow mode and keeps the spilled fields."""
    result = NepaliDate(2081, 4, 32).add_years(1, Overflow.SPILL)
    assert (result.year, result.month, result.day) == (2082, 5, 1)


def test_comparisons_between_two_dates_use_the_ordinal() -> None:
    """Two real dates compare by ordinal in all four directions."""
    first = NepaliDate(2080, 1, 1)
    second = NepaliDate(2080, 1, 2)
    assert first < second
    assert first <= second
    assert second > first
    assert second >= first


def test_format_with_an_empty_spec_is_str() -> None:
    """An empty format spec is the default display."""
    date = NepaliDate(2080, 5, 15)
    assert format(date, "") == str(date)


def test_format_ne_short_year_uses_the_last_two_digits() -> None:
    """``yy`` uses the year modulo 100, not another modulus."""
    assert NepaliDate(2081, 4, 15).format("yy", Lang.NE) == "८१"


def test_format_ne_day_without_padding_uses_the_day_table() -> None:
    """``d`` in a custom pattern is the unpadded day, not a missing value."""
    assert NepaliDate(2080, 5, 15).format("d MMMM", Lang.NE) == "१५ भदौ"


def test_format_ne_month_name_uses_the_month_table() -> None:
    """``MMMM`` is the full Nepali month name."""
    assert NepaliDate(2080, 5, 15).format("MMMM", Lang.NE) == "भदौ"


def test_format_with_two_quoted_literals_uses_the_first_closing_quote() -> None:
    """Two quoted literals are separate; the first closing quote ends the first one."""
    assert NepaliDate(2080, 5, 15).format("'a' 'b'") == "a b"


def test_from_serial_starts_the_next_month_at_its_exact_ordinal() -> None:
    """The month-start bucket advances when the ordinal equals the next start."""
    index = 13
    date = _from_serial(MONTH_START_ORD[index])
    assert (date.year, date.month, date.day) == (MONTH_YEAR[index], MONTH_NUM[index], 1)


def test_now_returns_an_aware_utc_instant() -> None:
    """The default clock is UTC, not the local zone."""
    assert _now().tzinfo is datetime.UTC


def test_fractional_timedelta_keeps_the_error_kind() -> None:
    """A timedelta with seconds is OUT_OF_RANGE, not an unkind error."""
    with pytest.raises(NepDateError) as caught:
        _ = NepaliDate(2080, 5, 15) + datetime.timedelta(seconds=1)
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE


def test_add_months_keeps_the_error_kind_when_a_spill_passes_the_range() -> None:
    """The last month cannot spill into a year after MAX."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate(2199, 12, 30).add_months(1, Overflow.SPILL)
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE


def test_fiscal_start_and_end_keep_their_fields() -> None:
    """The fiscal year boundaries are 1 Shrawan and the last day of Ashad."""
    fiscal = FiscalYear(2082)
    assert (fiscal.start().year, fiscal.start().month, fiscal.start().day) == (2082, 4, 1)
    end = fiscal.end()
    assert (end.year, end.month) == (2083, 3)
    assert end.day == end.month_length


def test_quarter_range_keeps_its_start_and_end_fields() -> None:
    """Every quarter starts on day 1 and ends on its last day."""
    fiscal = FiscalYear(2082)
    for quarter, year, month in (
        (Quarter.Q1, 2082, 4),
        (Quarter.Q2, 2082, 7),
        (Quarter.Q3, 2082, 10),
        (Quarter.Q4, 2083, 1),
    ):
        quarter_range = fiscal.quarter_range(quarter)
        assert (
            quarter_range.start.year,
            quarter_range.start.month,
            quarter_range.start.day,
        ) == (year, month, 1)
        assert quarter_range.end.month == (month + 2 - 1) % 12 + 1
        assert quarter_range.end.day == quarter_range.end.month_length


def test_fiscal_quarter_out_of_range_keeps_the_error_kind() -> None:
    """A quarter before the supported range is OUT_OF_RANGE."""
    with pytest.raises(NepDateError) as caught:
        FiscalYear(1900).quarter_range(Quarter.Q1)
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE


def test_fiscal_ne_label_pads_a_single_digit_year_suffix() -> None:
    """The year suffix is always two digits."""
    assert FiscalYear(2099).label(Lang.NE) == "२०९९/००"  # noqa: RUF001 - Devanagari digits


def test_parse_strict_accepts_the_last_devanagari_digit() -> None:
    """The digit ९ is a digit, not an invalid character."""
    assert NepaliDate.parse("२०८९/०५/१५") == NepaliDate(2089, 5, 15)


def test_parse_strict_five_digit_group_is_number_too_long() -> None:
    """A five-digit group reaches the scanner and is NUMBER_TOO_LONG."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.parse("20801/05/15")
    assert caught.value.kind is ErrorKind.NUMBER_TOO_LONG


def test_parse_strict_missing_group_is_wrong_group_count() -> None:
    """The scanner reports a missing group, not an index error."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.parse("2080/05")
    assert caught.value.kind is ErrorKind.WRONG_GROUP_COUNT


def test_lenient_error_kinds_are_reported() -> None:
    """Unknown words, two month names and bad year positions keep their kinds."""
    for text, kind in (
        ("15 Shrawan Bhadra 2080", ErrorKind.UNRECOGNIZED),
        ("15 notamonth 2080", ErrorKind.UNRECOGNIZED),
        ("15/04/80", ErrorKind.AMBIGUOUS),
        ("12345/01/01", ErrorKind.NUMBER_TOO_LONG),
    ):
        with pytest.raises(NepDateError) as caught:
            NepaliDate.parse_lenient(text)
        assert caught.value.kind is kind, text


def test_lenient_month_form_keeps_the_error_kind_for_a_bad_day() -> None:
    """A three-digit day after a month name is AMBIGUOUS."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.parse_lenient("100 Shrawan 2080")
    assert caught.value.kind is ErrorKind.AMBIGUOUS


def test_lenient_numeric_form_keeps_the_error_kind_without_a_year() -> None:
    """Three two-digit numbers are AMBIGUOUS."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.parse_lenient("15/04/80")
    assert caught.value.kind is ErrorKind.AMBIGUOUS


def test_lenient_dotted_number_starts_at_the_first_digit() -> None:
    """A dotted number is split at its dots, starting at the first character."""
    assert NepaliDate.parse_lenient("15.04.2080") == NepaliDate(2080, 4, 15)


def test_parse_strict_zero_padded_five_digit_year_is_number_too_long() -> None:
    """The fast path does not accept a five-digit group even when its value is a valid year."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.parse("02080/01/01")
    assert caught.value.kind is ErrorKind.NUMBER_TOO_LONG


def test_format_ne_month_without_padding_uses_the_digit_table() -> None:
    """``M`` in Nepali is the unpadded month in Devanagari digits."""
    assert NepaliDate(2080, 5, 15).format("M", Lang.NE) == "५"


def test_format_single_y_is_followed_by_the_next_token() -> None:
    """A one-character ``y`` run ends after itself; the next character is still read."""
    assert NepaliDate(2080, 5, 15).format("y-M") == "80-5"


def test_format_empty_quoted_literal_is_empty() -> None:
    """``''`` is an empty literal; the closing quote is the next character."""
    assert NepaliDate(2080, 5, 15).format("yyyy''MM") == "208005"


@pytest.mark.parametrize("compare", [operator.lt, operator.le, operator.gt, operator.ge])
def test_ordering_with_another_type_raises_type_error(
    compare: Callable[[object, object], bool],
) -> None:
    """Every ordering operator returns NotImplemented for a non-date, so Python raises."""
    with pytest.raises(TypeError):
        compare(NepaliDate(2080, 1, 1), "2080-01-01")


@pytest.mark.parametrize("args", [(2080, True, 1), (2080, 1, True), (True, 1, 1)])
def test_bool_in_any_position_is_rejected(args: tuple[int, int, int]) -> None:
    """``bool`` is rejected as the year, the month or the day, not read as 0 or 1."""
    with pytest.raises(TypeError):
        NepaliDate(*args)


def test_add_months_spill_past_the_last_month_is_out_of_range() -> None:
    """Day 32 of Ashad 2199 shifted to Chaitra 2199 (30 days) would spill into 2200."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate(2199, 3, 32).add_months(9, Overflow.SPILL)
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE


_RAISERS: tuple[Callable[[], object], ...] = (
    lambda: NepaliDate(1800, 1, 1),
    lambda: NepaliDate(2080, 13, 1),
    lambda: NepaliDate(2080, 1, 40),
    lambda: NepaliDate(True, 1, 1),
    lambda: NepaliDate.from_ordinal(0),
    lambda: NepaliDate(2080, 1, 1).add_months(10**6),
    lambda: NepaliDate(2199, 3, 32).add_months(9, Overflow.SPILL),
    lambda: NepaliDate(2080, 1, 1) + datetime.timedelta(seconds=1),
    lambda: NepaliDate(2080, 1, 1).short(order="x"),  # type: ignore[arg-type]
    lambda: DateRange(NepaliDate(2080, 1, 2), NepaliDate(2080, 1, 1)),
    lambda: FiscalYear(1800),
    lambda: FiscalYear(1900).start(),
    lambda: FiscalYear(2199).end(),
    lambda: FiscalYear(1900).quarter_range(Quarter.Q1),
    lambda: NepaliDate.parse("2080/01/01/01"),
    lambda: NepaliDate.parse("20801/05/15"),
    lambda: NepaliDate.parse("2080/0a/01"),
    lambda: NepaliDate.parse("2080/05"),
    lambda: NepaliDate.parse_lenient("15 notamonth 2080"),
    lambda: NepaliDate.parse_lenient("15 Shrawan Bhadra 2080"),
    lambda: NepaliDate.parse_lenient("1 2"),
    lambda: NepaliDate.parse_lenient("12345/01/01"),
    lambda: NepaliDate.parse_lenient("15 Shrawan 80"),
    lambda: NepaliDate.parse_lenient("100 Shrawan 2080"),
    lambda: NepaliDate.parse_lenient("15/04/80"),
    lambda: delattr(NepaliDate(2080, 1, 1).diff(NepaliDate(2080, 1, 2)), "days"),
)


@pytest.mark.parametrize("raiser", _RAISERS)
def test_every_error_carries_a_message(raiser: Callable[[], object]) -> None:
    """The wording is not API (docs/API.md matches on ``kind``), but no error is blank."""
    with pytest.raises((NepDateError, TypeError, ValueError, AttributeError)) as caught:
        raiser()
    message = str(caught.value)
    assert message
    assert message != "None"

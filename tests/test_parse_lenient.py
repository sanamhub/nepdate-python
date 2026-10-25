"""Lenient parse tests: PARSING §2, the vectors and the no-guessing rules."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nepdate import NepaliDate
from nepdate._errors import ErrorKind, NepDateError

_PARSE_ROWS = 69  # shared/spec/vectors/parse.tsv data rows.
_ERROR_KINDS = {
    "InvalidCharacter": ErrorKind.INVALID_CHARACTER,
    "WrongGroupCount": ErrorKind.WRONG_GROUP_COUNT,
    "NumberTooLong": ErrorKind.NUMBER_TOO_LONG,
    "Ambiguous": ErrorKind.AMBIGUOUS,
    "Unrecognized": ErrorKind.UNRECOGNIZED,
    "OutOfRange": ErrorKind.OUT_OF_RANGE,
    "InvalidMonth": ErrorKind.INVALID_MONTH,
    "InvalidDay": ErrorKind.INVALID_DAY,
}


def test_lenient_parse_vectors(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """Every row of parse.tsv matches its lenient column, success or error kind."""
    rows = vector_reader("parse.tsv")
    assert len(rows) == _PARSE_ROWS
    for row in rows:
        expected = row["lenient"]
        if expected.startswith("ERR:"):
            with pytest.raises(NepDateError) as caught:
                NepaliDate.parse_lenient(row["input"])
            assert caught.value.kind is _ERROR_KINDS[expected.removeprefix("ERR:")], row
        else:
            assert NepaliDate.parse_lenient(row["input"]).isoformat() == expected, row


def test_month_name_positions() -> None:
    """The year, month and day may appear in any order around one month name."""
    expected = NepaliDate(2080, 4, 15)
    for text in (
        "15 Shrawan 2080",
        "Shrawan 15, 2080",
        "2080 Shrawan 15",
        "15 साउन 2080",
        "१५ श्रावण २०८०",
    ):
        assert NepaliDate.parse_lenient(text) == expected, text


def test_numeric_forms() -> None:
    """Three numbers need a 4-digit year first or last; the middle is never the year."""
    assert NepaliDate.parse_lenient("2080/04/15") == NepaliDate(2080, 4, 15)
    assert NepaliDate.parse_lenient("15/04/2080") == NepaliDate(2080, 4, 15)
    assert NepaliDate.parse_lenient("15.04.2080") == NepaliDate(2080, 4, 15)


def test_no_permutation_guessing() -> None:
    """D-06: a month-first three-number form is not guessed; it fails as a day of 15."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.parse_lenient("04/15/2080")
    assert caught.value.kind is ErrorKind.INVALID_MONTH


def test_two_digit_year_is_ambiguous() -> None:
    """D-06: a two-digit year is never expanded."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.parse_lenient("15/04/80")
    assert caught.value.kind is ErrorKind.AMBIGUOUS


def test_era_markers_and_keywords() -> None:
    """Era markers and गते/मिति are dropped, in Latin and Devanagari."""
    expected = NepaliDate(2080, 4, 15)
    for text in (
        "2080/04/15 BS",
        "2080/04/15 B.S.",
        "2080/04/15 VS",
        "15 साउन, 2080 गते",
        "मिति 2080/04/15",
        "B.S. 2080 Shrawan 15",
        "२०८०/०४/१५ बि.सं.",
    ):
        assert NepaliDate.parse_lenient(text) == expected, text


def test_joiners_are_not_removed() -> None:
    """A month name with U+200C or U+200D inside is not a month name (PARSING §2)."""
    for joiner in ("\N{ZERO WIDTH NON-JOINER}", "\N{ZERO WIDTH JOINER}"):
        with pytest.raises(NepDateError) as caught:
            NepaliDate.parse_lenient(f"15 श्रा{joiner}वण 2080")
        assert caught.value.kind is ErrorKind.UNRECOGNIZED


def test_case_folding_is_exactly_python_lower_for_ascii() -> None:
    """The Kelvin sign folds to k; the long s and dotless i do not fold."""
    assert NepaliDate.parse_lenient("15 \u212aartik 2080") == NepaliDate(2080, 7, 15)
    with pytest.raises(NepDateError) as caught:
        NepaliDate.parse_lenient("15 \u017fhrawan 2080")
    assert caught.value.kind is ErrorKind.UNRECOGNIZED
    with pytest.raises(NepDateError) as caught:
        NepaliDate.parse_lenient("15 Ashw\u0131n 2080")
    assert caught.value.kind is ErrorKind.UNRECOGNIZED


def test_arabic_indic_digits_are_not_digits() -> None:
    """Arabic-Indic digits are letters to the lenient parser, so the token is unknown."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.parse_lenient("\u0662\u0660\u0668\u0660/\u0660\u0665/\u0661\u0665")
    assert caught.value.kind is ErrorKind.UNRECOGNIZED


def test_number_too_long() -> None:
    """A numeric token of more than four digits is rejected before any other rule."""
    for text in ("12345/01/01", "15 Shrawan 20800"):
        with pytest.raises(NepDateError) as caught:
            NepaliDate.parse_lenient(text)
        assert caught.value.kind is ErrorKind.NUMBER_TOO_LONG, text


def test_unrecognized_shapes() -> None:
    """Two month names, an unknown word, a wrong token count or empty input are Unrecognized."""
    for text in (
        "Shrawan Bhadra 2080",
        "15 Foo 2080",
        "2080/05",
        "2080",
        "2080/05/15/99",
        "not a date",
        "",
        " ",
    ):
        with pytest.raises(NepDateError) as caught:
            NepaliDate.parse_lenient(text)
        assert caught.value.kind is ErrorKind.UNRECOGNIZED, text


def test_validation_errors_keep_their_kind() -> None:
    """A parsed but invalid date raises the validation error of the strict constructor."""
    for text, kind in (
        ("2080/13/01", ErrorKind.INVALID_MONTH),
        ("2080/05/40", ErrorKind.INVALID_DAY),
        ("1900/12/30", ErrorKind.OUT_OF_RANGE),
    ):
        with pytest.raises(NepDateError) as caught:
            NepaliDate.parse_lenient(text)
        assert caught.value.kind is kind, text


@given(st.text(max_size=20))
def test_arbitrary_text_raises_only_nepdate_error(text: str) -> None:
    """Arbitrary text either parses or raises ``NepDateError``, never another exception."""
    try:
        NepaliDate.parse_lenient(text)
    except NepDateError:
        return

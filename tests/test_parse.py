"""Strict parse tests: PARSING §1, the vectors and the ASCII fast path (P3-04)."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nepdate import NepaliDate
from nepdate._errors import ErrorKind, NepDateError
from nepdate._parse import _fast_parse, _scan_strict

_PARSE_ROWS = 67  # P3-04 says 57; shared/spec/vectors/parse.tsv has 67 data rows.
_ERROR_KINDS = {
    "InvalidCharacter": ErrorKind.INVALID_CHARACTER,
    "WrongGroupCount": ErrorKind.WRONG_GROUP_COUNT,
    "NumberTooLong": ErrorKind.NUMBER_TOO_LONG,
    "OutOfRange": ErrorKind.OUT_OF_RANGE,
    "InvalidMonth": ErrorKind.INVALID_MONTH,
    "InvalidDay": ErrorKind.INVALID_DAY,
}
_PARSE_ALPHABET = (
    "0123456789/-._ \\|।"
    + "\u0966\u0967\u0968\u0969\u096a\u096b\u096c\u096d\u096e\u096f"
    + "abc\u0662\u00b2"
)


def test_strict_parse_vectors(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """Every row of parse.tsv matches its strict column, success or error kind."""
    rows = vector_reader("parse.tsv")
    assert len(rows) == _PARSE_ROWS
    for row in rows:
        expected = row["strict"]
        if expected.startswith("ERR:"):
            with pytest.raises(NepDateError) as caught:
                NepaliDate.parse(row["input"])
            assert caught.value.kind is _ERROR_KINDS[expected.removeprefix("ERR:")], row
        else:
            assert NepaliDate.parse(row["input"]).isoformat() == expected, row


def test_arabic_indic_digits_are_invalid() -> None:
    """Arabic-Indic digits are not ASCII or Devanagari, so the parser rejects them."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.parse("\u0662\u0660\u0668\u0660/\u0660\u0665/\u0661\u0665")
    assert caught.value.kind is ErrorKind.INVALID_CHARACTER


def test_ascii_only_digits_are_accepted() -> None:
    """ASCII and Devanagari digits parse; a mixed number is accepted (D-05)."""
    assert NepaliDate.parse("2080/05/15") == NepaliDate(2080, 5, 15)
    assert NepaliDate.parse("२०८०/०५/१५") == NepaliDate(2080, 5, 15)
    assert NepaliDate.parse("\u0968\u0966\u096e0/0\u096b/15") == NepaliDate(2080, 5, 15)


def test_unsafe_int_and_isdigit_paths_do_not_leak() -> None:
    """``_`` is a separator and a superscript is not a digit, so neither reaches ``int``."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.parse("2⁰80/05/15")
    assert caught.value.kind is ErrorKind.INVALID_CHARACTER
    assert NepaliDate.parse("2080_05_15") == NepaliDate(2080, 5, 15)


def test_fast_path_declines_everything_else() -> None:
    """Mixed, repeated, leading or trailing separators and non-ASCII go to the scanner."""
    for text in (
        "",
        "2080//05//15",
        "/2080/05/15/",
        "2080.05.15",
        "2080 05 15",
        "2080।05।15",
        "\u06f2\u06f0\u06f8\u06f0/\u06f0\u06f5/\u06f1\u06f5",
        "abc/def/ghi",
        "12345/01/01",
        "2080/13/01",
        "2080/05/15/99",
    ):
        assert _fast_parse(text, NepaliDate) is None, text


def test_fast_path_accepts_plain_three_group_input() -> None:
    """The fast path returns a date only for three ASCII digit groups on one separator."""
    assert _fast_parse("2080/05/15", NepaliDate) == NepaliDate(2080, 5, 15)
    assert _fast_parse("2080-5-1", NepaliDate) == NepaliDate(2080, 5, 1)
    assert _fast_parse("2080/05/15", NepaliDate).isoformat() == "2080-05-15"


@given(st.text(alphabet=_PARSE_ALPHABET, max_size=20))
def test_fast_path_agrees_with_the_scanner(text: str) -> None:
    """If the fast path returns, the scanner alone returns the same date (ADR-0002 §5)."""
    fast = _fast_parse(text, NepaliDate)
    if fast is not None:
        assert _scan_strict(text, NepaliDate) == fast


@given(st.text(max_size=20))
def test_arbitrary_text_raises_only_nepdate_error(text: str) -> None:
    """Arbitrary text either parses or raises ``NepDateError``, never another exception."""
    try:
        NepaliDate.parse(text)
    except NepDateError:
        return

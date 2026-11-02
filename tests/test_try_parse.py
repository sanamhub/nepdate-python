"""The non-throwing parsers: ``try_parse`` and ``try_parse_lenient`` (NP03, NP08)."""

from __future__ import annotations

from collections.abc import Callable

from nepdate import NepaliDate

_ERROR_KINDS = frozenset(
    {
        "InvalidCharacter",
        "WrongGroupCount",
        "NumberTooLong",
        "Ambiguous",
        "Unrecognized",
        "OutOfRange",
        "InvalidMonth",
        "InvalidDay",
    }
)


def test_try_parse_matches_the_strict_column(
    vector_reader: Callable[..., list[dict[str, str]]],
) -> None:
    """``try_parse`` returns a date exactly when the strict column is not an error."""
    for row in vector_reader("parse.tsv"):
        expected = row["strict"]
        found = NepaliDate.try_parse(row["input"])
        if expected.startswith("ERR:"):
            assert found is None, row
            assert expected.removeprefix("ERR:") in _ERROR_KINDS, row
        else:
            assert found is not None and found.isoformat() == expected, row


def test_try_parse_lenient_matches_the_lenient_column(
    vector_reader: Callable[..., list[dict[str, str]]],
) -> None:
    """``try_parse_lenient`` returns a date exactly when the lenient column is not an error."""
    for row in vector_reader("parse.tsv"):
        expected = row["lenient"]
        found = NepaliDate.try_parse_lenient(row["input"])
        if expected.startswith("ERR:"):
            assert found is None, row
            assert expected.removeprefix("ERR:") in _ERROR_KINDS, row
        else:
            assert found is not None and found.isoformat() == expected, row


def test_try_parse_never_raises_where_parse_raises() -> None:
    """The non-throwing forms cover the same ground as the raising ones."""
    for text in ("", "2080", "2080/05", "2080/05/15/99", "2081-01-32", "not a date", "2080/13/01"):
        assert NepaliDate.try_parse(text) is None, text
        assert NepaliDate.try_parse_lenient(text) is None, text
    assert NepaliDate.try_parse("2081/04/15") == NepaliDate(2081, 4, 15)
    assert NepaliDate.try_parse_lenient("15 Shrawan 2081") == NepaliDate(2081, 4, 15)


def test_try_parse_is_the_classmethod_not_a_module_function() -> None:
    """Both names are classmethods on ``NepaliDate``, as NP03 and NP08 name them."""
    assert NepaliDate.try_parse("2081-04-15") == NepaliDate(2081, 4, 15)
    assert NepaliDate.try_parse_lenient("2081-04-15") == NepaliDate(2081, 4, 15)

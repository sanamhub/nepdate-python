"""Format matrix: format-matrix.tsv (NF02, NF08, NF09, D-15)."""

from __future__ import annotations

from collections.abc import Callable

from nepdate import DateOrder, Lang, NepaliDate, Separator

_ROWS = 102
_SHORT_ROWS = 94
_TRY_FORMAT_ROWS = 8
_REFERENCE = "2081-04-15"


def _date(value: str) -> NepaliDate:
    year, month, day = value.split("-")
    return NepaliDate(int(year), int(month), int(day))


def test_format_matrix_short_rows(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """Every short row of format-matrix.tsv matches, including the D-15 Nepali rows.

    The ``try_format`` rows cover NF07, which a Python port does not have: formatting
    returns a new string, so there is no caller buffer to fill or overflow.
    """
    rows = vector_reader("csharp-golden", "format-matrix.tsv")
    assert len(rows) == _ROWS
    short_rows = [row for row in rows if row["kind"] == "short"]
    assert len(short_rows) == _SHORT_ROWS
    assert len(rows) - len(short_rows) == _TRY_FORMAT_ROWS
    for row in short_rows:
        date = _date(row["bs"])
        actual = date.short(
            DateOrder[row["order"].upper()],
            Separator[row["separator"].upper()],
            row["pad"] == "true",
            Lang[row["lang"].upper()],
        )
        assert actual == row["result"], row


def test_every_order_separator_and_pad_is_covered(
    vector_reader: Callable[..., list[dict[str, str]]],
) -> None:
    """The vector names every order, separator and pad choice for the reference date."""
    rows = vector_reader("csharp-golden", "format-matrix.tsv")
    covered = {
        (row["order"], row["separator"], row["pad"])
        for row in rows
        if row["kind"] == "short" and row["lang"] == "en" and row["bs"] == _REFERENCE
    }
    expected = {
        (order.name.lower().capitalize(), separator.name.lower().capitalize(), pad)
        for order in DateOrder
        for separator in Separator
        for pad in ("true", "false")
    }
    assert covered == expected

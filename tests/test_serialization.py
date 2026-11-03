"""JSON and pickle hooks: serialization.tsv and ``__reduce__`` (NC10, D-01, D-11)."""

from __future__ import annotations

import copy
import csv
import json
import pickle
from collections.abc import Callable

import pytest

from nepdate import NepaliDate
from nepdate._errors import NepDateError

_ROWS = 11


def _date(value: str) -> NepaliDate:
    year, month, day = value.split("-")
    return NepaliDate(int(year), int(month), int(day))


def test_serialization_vectors(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """Every row of serialization.tsv matches; a JSON null is refused (D-01)."""
    # The json column holds literal JSON text, quotes included, so the reader must not
    # treat a leading quote as a quoting mark.
    rows = vector_reader("csharp-golden", "serialization.tsv", quoting=csv.QUOTE_NONE)
    assert len(rows) == _ROWS
    for row in rows:
        if row["kind"] == "write":
            assert _date(row["input"]).to_json() == row["json"], row
        elif row["kind"] == "read":
            if row["result"] == "ERR":
                with pytest.raises(NepDateError):
                    NepaliDate.from_json(row["input"])
            else:
                assert NepaliDate.from_json(row["input"]) == _date(row["result"]), row
        else:
            date = _date(row["input"])
            assert NepaliDate.from_json(date.to_json()) == _date(row["result"]), row


def test_to_json_is_the_canonical_string() -> None:
    """The JSON text is the quoted canonical ``YYYY-MM-DD`` form."""
    assert NepaliDate(2081, 4, 15).to_json() == '"2081-04-15"'
    assert json.loads(NepaliDate(2081, 4, 15).to_json()) == "2081-04-15"


def test_from_json_accepts_surrounding_whitespace() -> None:
    """Whitespace around the value is not part of the string and is ignored."""
    assert NepaliDate.from_json('  "2081-04-15"\n') == NepaliDate(2081, 4, 15)


def test_from_json_refuses_every_non_string_value() -> None:
    """A JSON null, number, object or bare date is not a date string (D-01)."""
    for text in ("null", "2081", '""', "[]", '"2081-04-15', '2081-04-15"'):
        with pytest.raises(NepDateError):
            NepaliDate.from_json(text)


def test_fromisoformat_is_the_inverse_of_isoformat() -> None:
    """``fromisoformat`` parses the text ``isoformat`` writes, as on ``datetime.date``."""
    date = NepaliDate(2081, 4, 15)
    assert NepaliDate.fromisoformat(date.isoformat()) == date
    assert NepaliDate.fromisoformat("2081/04/15") == date
    with pytest.raises(NepDateError):
        NepaliDate.fromisoformat("not a date")


def test_pickle_and_copy_rebuild_the_same_date() -> None:
    """``__reduce__`` keeps the date equal through pickle and copy in both protocols."""
    date = NepaliDate(2081, 4, 15)
    for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
        assert pickle.loads(pickle.dumps(date, protocol)) == date
    assert copy.copy(date) == date
    assert copy.deepcopy(date) == date


def test_pickle_uses_the_constructor_form() -> None:
    """The reduce tuple names the class and the three fields, so the state is visible."""
    assert NepaliDate(2081, 4, 15).__reduce__() == (NepaliDate, (2081, 4, 15))


def test_json_roundtrip_sample(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """A round trip through both hooks returns the same date for every write row."""
    rows = vector_reader("csharp-golden", "serialization.tsv", quoting=csv.QUOTE_NONE)
    for row in rows:
        if row["kind"] != "write":
            continue
        date = _date(row["input"])
        assert NepaliDate.from_json(date.to_json()) == date

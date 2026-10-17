"""Formatting tests: ``__str__``, ``__repr__``, ``isoformat``, ``short`` and ``long`` (P3-02)."""

from __future__ import annotations

from collections.abc import Callable

from nepdate import Lang, NepaliDate
from nepdate._names import DateOrder, Separator

_BS_COLUMNS = (
    "to_string",
    "unicode",
    "long_en",
    "long_en_weekday",
    "long_ne",
    "long_ne_weekday",
    "dmy_dash_nopad",
)
_DEFAULT_LENGTH = 10


def _parse_bs(value: str) -> tuple[int, int, int]:
    year, month, day = value.split("-")
    return int(year), int(month), int(day)


def test_golden_format_columns(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """The seven formatting columns of the golden dates table match on every row."""
    rows = vector_reader("csharp-golden", "dates.tsv")
    for row in rows:
        date = NepaliDate(*_parse_bs(row["bs"]))
        actual = {
            "to_string": str(date),
            "unicode": date.short(lang=Lang.NE),
            "long_en": date.long(),
            "long_en_weekday": date.long(weekday=True),
            "long_ne": date.long(lang=Lang.NE),
            "long_ne_weekday": date.long(weekday=True, lang=Lang.NE),
            "dmy_dash_nopad": date.short(DateOrder.DMY, Separator.DASH, pad=False),
        }
        mismatch = {
            name: (actual[name], row[name]) for name in _BS_COLUMNS if actual[name] != row[name]
        }
        assert not mismatch, f"bs {row['bs']}: {mismatch}"


def test_str_and_isoformat() -> None:
    """``str`` is the default display and ``isoformat`` is the D-11 sortable form."""
    date = NepaliDate(2081, 4, 15)
    assert str(date) == "2081/04/15"
    assert date.isoformat() == "2081-04-15"


def test_str_is_ten_characters() -> None:
    """The default display is always ``YYYY/MM/DD``."""
    for parts in [(1901, 1, 1), (2080, 12, 30), (2199, 12, 30)]:
        assert len(str(NepaliDate(*parts))) == _DEFAULT_LENGTH


def test_repr() -> None:
    """``repr`` is the unambiguous constructor form."""
    assert repr(NepaliDate(2081, 4, 15)) == "NepaliDate(2081, 4, 15)"


def test_short_examples() -> None:
    """The three examples of FORMATTING §3 match."""
    date = NepaliDate(2080, 5, 15)
    assert date.short(DateOrder.YMD, Separator.DASH, pad=True, lang=Lang.EN) == "2080-05-15"
    assert date.short(DateOrder.DMY, Separator.DASH, pad=False, lang=Lang.EN) == "15-5-2080"
    assert date.short(DateOrder.YMD, Separator.SLASH, pad=True, lang=Lang.NE) == "२०८०/०५/१५"


def test_short_every_order_and_separator() -> None:
    """Each order writes the three fields in its own order with the chosen separator."""
    date = NepaliDate(2080, 5, 15)
    fields = {
        DateOrder.YMD: ("2080", "05", "15"),
        DateOrder.YDM: ("2080", "15", "05"),
        DateOrder.MYD: ("05", "2080", "15"),
        DateOrder.MDY: ("05", "15", "2080"),
        DateOrder.DYM: ("15", "2080", "05"),
        DateOrder.DMY: ("15", "05", "2080"),
    }
    for order, parts in fields.items():
        for separator in Separator:
            expected = separator.value.join(parts)
            assert date.short(order, separator) == expected


def test_short_padding() -> None:
    """``pad`` controls month and day only; the year is always four digits."""
    date = NepaliDate(1901, 1, 5)
    assert date.short() == "1901/01/05"
    assert date.short(pad=False) == "1901/1/5"
    assert date.short(DateOrder.DMY, Separator.DASH, pad=False, lang=Lang.NE) == "५-१-१९०१"


def test_long_examples() -> None:
    """The four examples of FORMATTING §4 match in both languages."""
    date = NepaliDate(2081, 4, 15)
    assert date.long() == "Shrawan 15, 2081"
    assert date.long(weekday=True) == "Tuesday, Shrawan 15, 2081"
    assert date.long(lang=Lang.NE) == "साउन १५, २०८१"
    assert date.long(weekday=True, lang=Lang.NE) == "मङ्गलवार, साउन १५, २०८१"

    first = NepaliDate(1901, 1, 1)
    assert first.long() == "Baishakh 01, 1901"
    assert first.long(lang=Lang.NE) == "बैशाख ०१, १९०१"

    short = NepaliDate(2079, 2, 6)
    assert short.long(weekday=True, year=False, pad=False) == "Friday, Jestha 6"
    assert short.long(weekday=True, year=False, pad=False, lang=Lang.NE) == "शुक्रवार, जेठ ६"


def test_long_option_combinations() -> None:
    """``year`` and ``pad`` act independently of ``weekday``."""
    date = NepaliDate(2079, 2, 6)
    assert date.long() == "Jestha 06, 2079"
    assert date.long(pad=False) == "Jestha 6, 2079"
    assert date.long(year=False) == "Jestha 06"
    assert date.long(weekday=True, year=False) == "Friday, Jestha 06"
    assert date.long(weekday=True, pad=False) == "Friday, Jestha 6, 2079"


def test_nepali_output_has_no_ascii_digits() -> None:
    """A missed digit mapping would leave an ASCII digit in Nepali output."""
    date = NepaliDate(2081, 4, 15)
    for text in (date.short(lang=Lang.NE), date.long(lang=Lang.NE)):
        assert not any("0" <= char <= "9" for char in text)
    assert any("0" <= char <= "9" for char in date.short(lang=Lang.EN))

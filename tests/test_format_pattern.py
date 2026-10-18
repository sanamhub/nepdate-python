"""Pattern formatting tests: ``format`` and ``__format__`` (P3-03, FORMATTING §5)."""

from __future__ import annotations

from collections.abc import Callable

from nepdate import Lang, NepaliDate, to_nepali_digits

_ROWS = 451
_D04_SKIPPED = 7
_MMM_RUN = 3


def _parse_bs(value: str) -> tuple[int, int, int]:
    year, month, day = value.split("-")
    return int(year), int(month), int(day)


def _has_mmm_token(pattern: str) -> bool:
    """Return whether ``pattern`` contains a token run of exactly three ``M``.

    Args:
        pattern: The format pattern.

    Returns:
        True when an unquoted, unescaped run of exactly three ``M`` occurs.
    """
    index = 0
    length = len(pattern)
    while index < length:
        char = pattern[index]
        if char == "\\":
            index += 2
            continue
        if char == "'":
            end = pattern.find("'", index + 1)
            index = length if end < 0 else end + 1
            continue
        if char == "M":
            end = index
            while end < length and pattern[end] == "M":
                end += 1
            if end - index == _MMM_RUN:
                return True
            index = end
            continue
        index += 1
    return False


def test_golden_format_patterns(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """Every golden pattern row matches, skipping only the seven D-04 rows."""
    rows = vector_reader("csharp-golden", "format-pattern.tsv")
    assert len(rows) == _ROWS
    skipped = 0
    for row in rows:
        date = NepaliDate(*_parse_bs(row["bs"]))
        if _has_mmm_token(row["pattern"]) and date.month in (3, 6):
            # D-04: C# writes "Ash" for both Ashad and Ashoj; the port writes Asa and Aso.
            skipped += 1
            continue
        actual = date.format(row["pattern"])
        assert actual == row["result"], f"{row['bs']} {row['pattern']!r}: {actual!r}"
    assert skipped == _D04_SKIPPED


def test_d04_pattern_abbreviations() -> None:
    """The skipped D-04 rows would expect Ash; the port writes the distinct Asa and Aso."""
    assert NepaliDate(2081, 3, 15).format("MMM") == "Asa"
    assert NepaliDate(2081, 6, 15).format("MMM") == "Aso"
    assert "Ash" not in NepaliDate(2081, 3, 15).format("MMM yyyy")
    assert "Ash" not in NepaliDate(2081, 6, 15).format("MMM yyyy")


def test_formatting_examples() -> None:
    """The six examples of FORMATTING §5 match."""
    date = NepaliDate(2081, 4, 15)
    assert date.format("yyyy-MM-dd") == "2081-04-15"
    assert date.format("M/d/yyyy") == "4/15/2081"
    assert date.format("yyyy'BS'") == "2081BS"
    assert date.format("yyyy\\M\\M-\\d\\d") == "2081MM-dd"
    assert date.format("MMM yyyy") == "Shr 2081"
    assert date.format("dd.MM.yy") == "15.04.81"


def test_standard_patterns() -> None:
    """``""``, ``G``, ``g`` and ``d`` are the default display; ``D`` and ``s`` are long and ISO."""
    date = NepaliDate(2081, 4, 15)
    for pattern in ("", "G", "g", "d"):
        assert date.format(pattern) == "2081/04/15"
    assert date.format("D") == "Shrawan 15, 2081"
    assert date.format("s") == "2081-04-15"


def test_standard_patterns_nepali() -> None:
    """The standard patterns localise their digits and names."""
    date = NepaliDate(2081, 4, 15)
    for pattern in ("", "G", "g", "d"):
        assert date.format(pattern, Lang.NE) == "२०८१/०४/१५"
    assert date.format("D", Lang.NE) == "साउन १५, २०८१"
    assert date.format("s", Lang.NE) == "२०८१-०४-१५"


def test_custom_pattern_tokens() -> None:
    """Runs of y, M and d pick the token of FORMATTING §5."""
    date = NepaliDate(2081, 4, 5)
    assert date.format("y") == "81"
    assert date.format("yy") == "81"
    assert date.format("yyy") == "81"
    assert date.format("yyyy") == "2081"
    assert date.format("yyyyy") == "2081"
    assert date.format("M") == "4"
    assert date.format("MM") == "04"
    assert date.format("MMM") == "Shr"
    assert date.format("MMMM") == "Shrawan"
    assert date.format("MMMMM") == "Shrawan"
    assert date.format("dd") == "05"
    assert date.format("d.") == "5."
    assert date.format("ddd") == "5"
    assert date.format("dddd") == "5"


def test_pattern_literals_and_escapes() -> None:
    """Quotes and backslashes write literals; a trailing backslash writes nothing."""
    date = NepaliDate(2081, 4, 5)
    assert date.format("yyyy'T'MM") == "2081T04"
    assert date.format("yyyy'BS") == "2081BS"
    assert date.format("yyyy\\-MM\\-dd") == "2081-04-05"
    assert date.format("yyyy\\") == "2081"
    assert date.format("'2'yy") == "281"


def test_pattern_localises_tokens_not_literals() -> None:
    """Token digits are Nepali; a literal stays exactly as written."""
    date = NepaliDate(2081, 4, 15)
    assert date.format("yyyy-MM-dd", Lang.NE) == "२०८१-०४-१५"
    assert date.format("MMM", Lang.NE) == "साउन"
    assert date.format("'x'yyyy", Lang.NE) == "x" + to_nepali_digits(2081)
    assert date.format("'२०'yyyy", Lang.NE) == "२०२०८१"


def test_dunder_format() -> None:
    """``__format__`` is ``format`` with English; an empty spec is ``str``."""
    date = NepaliDate(2081, 4, 15)
    assert f"{date}" == str(date)
    assert f"{date:s}" == "2081-04-15"
    assert f"{date:D}" == "Shrawan 15, 2081"
    assert f"{date:yyyy-MM-dd}" == "2081-04-15"
    assert f"{date:XXXX}" == "XXXX"
    assert f"{date:yyyy'BS'}" == "2081BS"
    assert format(date, "") == str(date)


def test_no_ascii_digits_in_nepali_pattern() -> None:
    """A missed digit mapping would leave an ASCII digit in a Nepali pattern output."""
    text = NepaliDate(2081, 4, 15).format("yyyy-MM-dd", Lang.NE)
    assert not any("0" <= char <= "9" for char in text)

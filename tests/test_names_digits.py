"""Tests for the month and weekday names and ``to_nepali_digits`` (P3-01)."""

from __future__ import annotations

from nepdate import Lang, Month, Weekday, to_nepali_digits

_MONTHS_EN = (
    "Baishakh",
    "Jestha",
    "Ashad",
    "Shrawan",
    "Bhadra",
    "Ashoj",
    "Kartik",
    "Mangsir",
    "Poush",
    "Magh",
    "Falgun",
    "Chaitra",
)
_MONTHS_NE = (
    "बैशाख",
    "जेठ",
    "असार",
    "साउन",
    "भदौ",
    "असोज",
    "कार्तिक",
    "मंसिर",
    "पुष",
    "माघ",
    "फागुन",
    "चैत",
)
_MONTHS_EN_SHORT = (
    "Bai",
    "Jes",
    "Asa",
    "Shr",
    "Bha",
    "Aso",
    "Kar",
    "Man",
    "Pou",
    "Mag",
    "Fal",
    "Cha",
)
_WEEKDAYS_EN = (
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
)
_WEEKDAYS_EN_SHORT = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")
_WEEKDAYS_NE = (
    "आइतवार",
    "सोमवार",
    "मङ्गलवार",
    "बुधवार",
    "बिहिवार",
    "शुक्रवार",
    "शनिवार",
)
_WEEKDAYS_NE_SHORT = ("आइत", "सोम", "मङ्गल", "बुध", "बिहि", "शुक्र", "शनि")


def test_month_full_names() -> None:
    """Every month has the English and Nepali full name of FORMATTING §1."""
    for month, english, nepali in zip(Month, _MONTHS_EN, _MONTHS_NE, strict=True):
        assert month.label() == english
        assert month.label(Lang.EN) == english
        assert month.label(Lang.NE) == nepali


def test_month_short_names() -> None:
    """Short English names follow FORMATTING §1; Nepali short names are the full names."""
    for month, short, nepali in zip(Month, _MONTHS_EN_SHORT, _MONTHS_NE, strict=True):
        assert month.short_label() == short
        assert month.short_label(Lang.NE) == nepali


def test_d04_ashad_and_ashoj_are_not_ash() -> None:
    """D-04: Ashad and Ashoj keep distinct abbreviations, not the C# ``Ash`` for both."""
    assert Month.ASHAD.short_label() == "Asa"
    assert Month.ASHOJ.short_label() == "Aso"
    assert Month.ASHAD.short_label() != "Ash"
    assert Month.ASHOJ.short_label() != "Ash"


def test_weekday_names() -> None:
    """Every weekday has the English and Nepali full and short names."""
    for weekday, english, short, nepali, nepali_short in zip(
        Weekday, _WEEKDAYS_EN, _WEEKDAYS_EN_SHORT, _WEEKDAYS_NE, _WEEKDAYS_NE_SHORT, strict=True
    ):
        assert weekday.label() == english
        assert weekday.short_label() == short
        assert weekday.label(Lang.NE) == nepali
        assert weekday.short_label(Lang.NE) == nepali_short


def test_to_nepali_digits() -> None:
    """The AC example and the ten digits map to U+0966 through U+096F."""
    assert to_nepali_digits(2081) == "२०८१"
    assert to_nepali_digits(1234567890) == "१२३४५६७८९०"
    assert to_nepali_digits(0) == "\u0966"


def test_to_nepali_digits_min_width() -> None:
    """``min_width`` zero-pads the ASCII string before translating it."""
    assert to_nepali_digits(5, 2) == "०५"
    assert to_nepali_digits(5, 4) == "०००५"
    assert to_nepali_digits(2081, 2) == "२०८१"


def test_to_nepali_digits_has_no_ascii_digit() -> None:
    """The output contains no ASCII digit, so a missed mapping cannot pass unnoticed."""
    translated = to_nepali_digits(1234567890)
    assert not any("0" <= char <= "9" for char in translated)

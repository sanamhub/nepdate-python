"""One test per C# catalogue row tagged phase 4."""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

import pytest

from nepdate import ErrorKind, NepaliDate, NepDateError
from nepdate_patro import CalendarInfo, Tithi, _tables, coverage, info, public_holidays

_PHASE_4_ROWS = 40


def _test_name(catalog_id: str) -> str:
    """Map a catalogue row id to its test function name.

    Args:
        catalog_id: The catalogue ``id``.

    Returns:
        ``test_`` plus the id lower-cased with every non-alphanumeric character as ``_``.
    """
    lowered = catalog_id.lower()
    sanitized = "".join(ch if ("a" <= ch <= "z") or ("0" <= ch <= "9") else "_" for ch in lowered)
    return "test_" + sanitized


def _catalog_rows(repo_root: Path) -> list[dict[str, str]]:
    """Read the catalogue rows, skipping its comment line.

    Args:
        repo_root: The repository root directory.

    Returns:
        One dictionary per data row, keyed by the header line.
    """
    path = repo_root / "shared" / "spec" / "vectors" / "csharp-tests" / "catalog.tsv"
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue
        if header is None:
            header = line.split("\t")
            continue
        rows.append(dict(zip(header, line.split("\t"), strict=True)))
    return rows


def _assert_out_of_range(d: datetime.date) -> None:
    """Assert ``NepaliDate.from_date(d)`` raises ``OUT_OF_RANGE``.

    Args:
        d: The AD date or datetime.
    """
    with pytest.raises(NepDateError) as caught:
        NepaliDate.from_date(d)
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE


def test_all_phase_4_rows_have_a_test(repo_root: Path) -> None:
    """Every catalogue row tagged phase 4 has a test named after its id."""
    rows = [row for row in _catalog_rows(repo_root) if row["phase"] == "4"]
    assert len(rows) == _PHASE_4_ROWS
    module = sys.modules[__name__]
    missing = [row["id"] for row in rows if not hasattr(module, _test_name(row["id"]))]
    assert not missing, f"phase 4 rows without a test: {missing}"


# --- Core/CalendarDataTests.cs ---


def test_calendardatatests_calendarstrings_pool_isnonempty() -> None:
    """The name pools are not empty."""
    assert _tables.TITHI_NAMES
    assert _tables.NAMES


def test_calendardatatests_calendarstrings_pool_allentrieshavenonemptynpanden() -> None:
    """Every name pool entry has a non-empty Nepali and English string."""
    for np, en in _tables.TITHI_NAMES + _tables.NAMES:
        assert np
        assert en


def test_calendardatatests_calendaroffsets_monthstart_hasexpectedlength() -> None:
    """C# CalendarOffsets has no Python equivalent; the core's month tables are generated."""
    pytest.skip("n/a: C# CalendarOffsets internal")


def test_calendardatatests_calendaroffsets_monthstart_isstrictlymonotonic() -> None:
    """C# CalendarOffsets has no Python equivalent; the core's month tables are generated."""
    pytest.skip("n/a: C# CalendarOffsets internal")


def test_calendardatatests_calendaroffsets_totaldays_matchesexpectedcount() -> None:
    """C# CalendarOffsets has no Python equivalent; coverage is 2793 days instead."""
    pytest.skip("n/a: C# CalendarOffsets internal")


def test_calendardatatests_tithidata_dayoffsets_isstrictlysorted() -> None:
    """The dense tithi index covers one contiguous day range."""
    assert len(_tables.TITHI_INDEX) == 2190
    last = NepaliDate(2083, 12, 30).to_ordinal()
    assert _tables.TITHI_FIRST + len(_tables.TITHI_INDEX) - 1 == last


def test_calendardatatests_tithidata_allpoolids_areinrange() -> None:
    """Every tithi index points into the 32-name table."""
    assert max(_tables.TITHI_INDEX) < len(_tables.TITHI_NAMES)


def test_calendardatatests_tithidata_entrycount_matches2190() -> None:
    """The tithi index has 2190 entries."""
    assert len(_tables.TITHI_INDEX) == 2190


def test_calendardatatests_eventdata_dayoffsets_isstrictlysorted() -> None:
    """Event days are strictly increasing."""
    assert list(_tables.EVENT_DAYS) == sorted(set(_tables.EVENT_DAYS))


def test_calendardatatests_eventdata_slicestart_isnondecreasing() -> None:
    """Event spans are contiguous and non-decreasing."""
    previous = 0
    for start, end in _tables.EVENT_SPANS:
        assert start == previous
        assert start < end
        previous = end


def test_calendardatatests_eventdata_slicestart_sentinelequalsentrieslength() -> None:
    """The last span ends at the event id count and there is one span per event day."""
    assert len(_tables.EVENT_SPANS) == len(_tables.EVENT_DAYS)
    assert _tables.EVENT_SPANS[-1][1] == len(_tables.EVENT_IDS)


def test_calendardatatests_eventdata_allentries_areinrange() -> None:
    """Every event id points into the name table."""
    assert all(index < len(_tables.NAMES) for index in _tables.EVENT_IDS)


def test_calendardatatests_eventdata_daycount_matches1671() -> None:
    """There are 1671 event days."""
    assert len(_tables.EVENT_DAYS) == 1671


def test_calendardatatests_holidaydata_dayoffsets_isstrictlysorted() -> None:
    """Holidays are strictly increasing."""
    assert list(_tables.HOLIDAYS) == sorted(set(_tables.HOLIDAYS))


def test_calendardatatests_holidaydata_count_matches294() -> None:
    """There are 294 public holidays."""
    assert len(_tables.HOLIDAYS) == 294


def test_calendardatatests_calendaroffsets_getoffset_baseyear_month1_day1_returnszero() -> None:
    """C# CalendarOffsets has no Python equivalent."""
    pytest.skip("n/a: C# CalendarOffsets internal")


def test_calendardatatests_calendaroffsets_getoffset_outofrange_returnsnegativeone() -> None:
    """C# CalendarOffsets has no Python equivalent."""
    pytest.skip("n/a: C# CalendarOffsets internal")


def test_calendardatatests_calendaroffsets_getoffset_alloffsetsareuniquesentinel() -> None:
    """C# CalendarOffsets has no Python equivalent."""
    pytest.skip("n/a: C# CalendarOffsets internal")


def test_calendardatatests_nepalidate_2081_01_01_calendardata() -> None:
    """2081-01-01 has the Panchami tithi, is a holiday and has three events."""
    result = info(NepaliDate(2081, 1, 1))
    assert result.tithi == Tithi("पञ्चमी", "Panchami")
    assert result.is_public_holiday is True
    assert tuple(event.en for event in result.events) == (
        "New Year",
        "Mesh Sankranti",
        "Bisket Jatra",
    )


def test_calendardatatests_nepalidate_2081_01_02_tithi_isshashthi() -> None:
    """2081-01-02 is Shashthi and has no events."""
    result = info(NepaliDate(2081, 1, 2))
    assert result.tithi == Tithi("षष्ठी", "Shashthi")
    assert result.events == ()
    assert result.is_public_holiday is False


def test_calendardatatests_nepalidate_2081_01_05_ispublicholiday() -> None:
    """2081-01-05 is a public holiday."""
    assert info(NepaliDate(2081, 1, 5)).is_public_holiday is True


def test_calendardatatests_nepalidate_2081_02_15_ispublicholiday_ganatantradiwas() -> None:
    """2081-02-15 is Republic Day and a public holiday."""
    result = info(NepaliDate(2081, 2, 15))
    assert result.is_public_holiday is True
    assert "Republic Day" in tuple(event.en for event in result.events)


def test_calendardatatests_nepalidate_2080_11_01_calendardata() -> None:
    """2080-11-01 is Chaturthi with the five events of the anchor table."""
    result = info(NepaliDate(2080, 11, 1))
    assert result.tithi == Tithi("चतुर्थी", "Chaturthi")
    assert tuple(event.en for event in result.events) == (
        "Mangala Chauthi Brata",
        "People's War Day",
        "Tilakund Chauthi",
        "Kumbha Sankranti",
        "World Radio Day",
    )


def test_calendardatatests_nepalidate_beforerange_allpropertiesreturndefaults() -> None:
    """A date before coverage returns the empty CalendarInfo."""
    result = info(NepaliDate(2070, 6, 15))
    assert result == CalendarInfo(None, False, ())
    assert result.tithi is None
    assert result.is_public_holiday is False
    assert result.events == ()


def test_calendardatatests_nepalidate_afterrange_allpropertiesreturndefaults() -> None:
    """A date after coverage returns the empty CalendarInfo."""
    result = info(NepaliDate(2090, 1, 1))
    assert result == CalendarInfo(None, False, ())
    assert result.tithi is None
    assert result.is_public_holiday is False
    assert result.events == ()


def test_calendardatatests_nepalidate_outsidetithirange_tithiisempty() -> None:
    """2077-01-01 is inside coverage but before the tithi range, so the tithi is empty."""
    result = info(NepaliDate(2077, 1, 1))
    assert result.tithi is None
    assert result.is_public_holiday is True


def test_calendardatatests_nepalidate_eventsnp_and_eventsen_alwayshavesamelength() -> None:
    """Every event carries both labels."""
    for date in coverage():
        for event in info(date).events:
            assert event.np
            assert event.en


def test_calendardatatests_getcalendarinfo_tithimatchesflatproperties() -> None:
    """The tithi from ``info`` is the table entry for that day."""
    date = NepaliDate(2081, 1, 1)
    index = _tables.TITHI_INDEX[date.to_ordinal() - _tables.TITHI_FIRST]
    assert info(date).tithi == Tithi(*_tables.TITHI_NAMES[index])


def test_calendardatatests_alldaysinscrapedrange_offsetsareinbounds() -> None:
    """Every coverage day has a valid entry and indices in bounds."""
    for date in coverage():
        result = info(date)
        if result.tithi is not None:
            assert (result.tithi.np, result.tithi.en) in _tables.TITHI_NAMES
        for event in result.events:
            assert (event.np, event.en) in _tables.NAMES


def test_calendardatatests_alldaysinscrapedrange_noexceptiononpropertyaccess() -> None:
    """Accessing every field of every coverage day raises nothing."""
    for date in coverage():
        result = info(date)
        assert result.is_public_holiday in (True, False)
        assert isinstance(result.events, tuple)
        if result.tithi is not None:
            assert result.tithi.np


def test_calendardatatests_alltithientries_resolvetononemptystrings() -> None:
    """Every tithi name has a non-empty Nepali string."""
    for np, _en in _tables.TITHI_NAMES:
        assert np


def test_calendardatatests_allholidayoffsets_areinbounds() -> None:
    """Every holiday ordinal is inside coverage."""
    assert all(
        _tables.COVERAGE_FIRST <= ordinal <= _tables.COVERAGE_LAST for ordinal in _tables.HOLIDAYS
    )


def test_calendardatatests_alleventoffsets_areinbounds() -> None:
    """Every event day ordinal is inside coverage."""
    assert all(
        _tables.COVERAGE_FIRST <= ordinal <= _tables.COVERAGE_LAST for ordinal in _tables.EVENT_DAYS
    )


def test_calendardatatests_holidaycount_viaapi_matches294() -> None:
    """The API yields the same 294 holidays as the table."""
    assert len(list(public_holidays())) == 294


def test_calendardatatests_calendarinfo_eventarrays_arenevernull() -> None:
    """Every CalendarInfo has a tuple of events, even when empty."""
    for date in coverage():
        assert isinstance(info(date).events, tuple)


# --- Extensions/DateTimeExtensionsTests.cs ---


def test_datetimeextensionstests_tonepalidate_validdatetime_returnscorrectnepalidate() -> None:
    """A datetime converts by its date part."""
    moment = datetime.datetime(2023, 4, 14, 10, 30)
    assert NepaliDate.from_date(moment) == NepaliDate(2080, 1, 1)


def test_datetimeextensionstests_tonepalidate_minvalue_throwsargumentoutofrangeexception() -> None:
    """``datetime.datetime.min`` is out of the supported range."""
    _assert_out_of_range(datetime.datetime.min)


def test_datetimeextensionstests_tonepalidate_maxvalue_throwsargumentoutofrangeexception() -> None:
    """``datetime.datetime.max`` is out of the supported range."""
    _assert_out_of_range(datetime.datetime.max)


def test_datetimeextensionstests_tonepalidate_datebeforeminsupported_throwsargumentoutofrangeexception() -> (
    None
):
    """1844-04-10 is one day before MIN."""
    _assert_out_of_range(datetime.date(1844, 4, 10))


def test_datetimeextensionstests_tonepalidate_dateaftermaxsupported_throwsargumentoutofrangeexception() -> (
    None
):
    """2143-04-16 is one day after MAX."""
    _assert_out_of_range(datetime.date(2143, 4, 16))

"""Unit tests for ``scripts/codegen.py``."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, cast

import pytest

from nepdate import NepaliDate

_MONTHS = 3588
_MONTH_BOUNDARIES = 3589
_YEARS = 300
_TOTAL_DAYS = 109212
_BUCKETS = 3413
_OFFSET = 673243
_TITHI_DAYS = 2190
_TITHI_NAMES = 32
_HOLIDAYS = 294
_EVENT_DAYS = 1671
_EVENT_IDS = 3032
_EVENT_NAMES = 721
_ALL_NAMES = 753
_INVISIBLE = "\N{ZERO WIDTH NON-JOINER}"


def _shipped_calendar(codegen: Any) -> dict[str, Any]:
    """Load a copy of the shipped calendar JSON.

    Args:
        codegen: The loaded codegen module.

    Returns:
        The parsed calendar data.
    """
    raw = json.loads(codegen.CALENDAR_JSON.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw)


def test_validate_accepts_shipped_data(codegen: Any) -> None:
    """The shipped calendar passes validation without raising."""
    codegen.validate_calendar(_shipped_calendar(codegen))


def test_validate_rejects_length_33(codegen: Any) -> None:
    """A month length of 33 is rejected."""
    data = _shipped_calendar(codegen)
    data["month_lengths"]["1901"][0] = 33
    with pytest.raises(ValueError):
        codegen.validate_calendar(data)


def test_generate_is_deterministic(codegen: Any) -> None:
    """The rendered module is byte for byte stable."""
    data = _shipped_calendar(codegen)
    assert codegen.generate_calendar_py(data) == codegen.generate_calendar_py(data)


def test_generated_calendar_matches_file(codegen: Any) -> None:
    """The on-disk ``_calendar.py`` matches what the generator would write."""
    data = _shipped_calendar(codegen)
    assert codegen.CALENDAR_PY.read_text(encoding="utf-8") == codegen.generate_calendar_py(data)


def test_generate_tables_match_acceptance_counts(codegen: Any) -> None:
    """The generated tables have the sizes ADR-0002 §3 promises."""
    data = _shipped_calendar(codegen)
    lengths = codegen.build_month_lengths(data)
    starts = codegen.build_month_starts(lengths)
    years = codegen.build_year_starts(starts)
    bucket = codegen.build_bucket(starts)
    assert len(lengths) == _MONTHS
    assert len(starts) == _MONTH_BOUNDARIES
    assert len(years) == _YEARS
    assert years[-1] == starts[-1] == _TOTAL_DAYS
    assert len(bucket) == _BUCKETS
    assert codegen.build_ordinal_offset(data) == _OFFSET


def test_bucket_two_step_bound_holds(codegen: Any) -> None:
    """The shipped data satisfies the two-step bucket bound without raising."""
    data = _shipped_calendar(codegen)
    lengths = codegen.build_month_lengths(data)
    bucket = codegen.build_bucket(codegen.build_month_starts(lengths))
    assert len(bucket) == _BUCKETS


def test_bucket_rejects_bad_month_starts(codegen: Any) -> None:
    """A serial more than two months past its block start raises ValueError.

    ``build_bucket`` must reject a table that would need more than two
    steps, so the bound check can fail when the generator is wrong.
    """
    with pytest.raises(ValueError):
        codegen.build_bucket(list(range(40)))


def test_main_returns_nonzero_on_bad_table(codegen: Any, tmp_path: Path, monkeypatch: Any) -> None:
    """A calendar whose generation fails makes ``main`` exit non-zero."""
    data = _shipped_calendar(codegen)
    data["month_lengths"]["1901"][0] = 1
    bad = tmp_path / "bs-calendar.json"
    bad.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(codegen, "CALENDAR_JSON", bad)
    assert codegen.main([]) == 1


def _shipped_patro(codegen: Any) -> dict[str, dict[str, Any]]:
    """Load a copy of the shipped patro days.

    Args:
        codegen: The loaded codegen module.

    Returns:
        The day text keyed to its parsed JSON object.
    """
    return cast(dict[str, dict[str, Any]], codegen.load_patro())


def _patro_tables(codegen: Any, days: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build the patro tables from the shipped calendar and patro data.

    Args:
        codegen: The loaded codegen module.
        days: Optional day data; defaults to the shipped copy.

    Returns:
        The table dictionary.
    """
    if days is None:
        days = _shipped_patro(codegen)
    return cast(dict[str, Any], codegen.build_patro_tables(days, _shipped_calendar(codegen)))


def test_patro_acceptance_counts(codegen: Any) -> None:
    """The generated patro tables have the sizes PATRO §3 promises."""
    tables = _patro_tables(codegen)
    assert len(tables["tithi_index"]) == _TITHI_DAYS
    assert len(tables["tithi_names"]) == _TITHI_NAMES
    assert len(tables["holidays"]) == _HOLIDAYS
    assert len(tables["event_days"]) == _EVENT_DAYS
    assert len(tables["event_ids"]) == _EVENT_IDS
    assert len(tables["names"]) == _EVENT_NAMES
    assert len(set(tables["tithi_names"]) | set(tables["names"])) == _ALL_NAMES


def test_patro_coverage_and_tithi_range(codegen: Any) -> None:
    """Coverage and tithi range are the ordinals of the dates PATRO §2 and §3 name."""
    tables = _patro_tables(codegen)
    assert tables["coverage_first"] == NepaliDate(2077, 1, 1).to_ordinal()
    assert tables["coverage_last"] == NepaliDate(2084, 8, 20).to_ordinal()
    assert tables["tithi_first"] == NepaliDate(2078, 1, 2).to_ordinal()
    assert tables["tithi_first"] + _TITHI_DAYS - 1 == NepaliDate(2083, 12, 30).to_ordinal()


def test_patro_event_order_and_spans(codegen: Any) -> None:
    """Event ids keep file order and the spans are contiguous."""
    tables = _patro_tables(codegen)
    names = tables["names"]
    first = tables["event_days"][0]
    assert first == NepaliDate(2077, 1, 1).to_ordinal()
    assert tables["event_spans"][0][0] == 0
    assert tables["event_spans"][-1][1] == len(tables["event_ids"])
    previous = 0
    for start, end in tables["event_spans"]:
        assert start == previous
        assert start < end
        previous = end
    ids = tables["event_ids"][tables["event_spans"][0][0] : tables["event_spans"][0][1]]
    assert [names[index][1] for index in ids] == [
        "New Year 2077",
        "Mesh Sankranti",
        "Bisket Jatra",
    ]


def test_missing_tithi_is_rejected(codegen: Any) -> None:
    """A gap inside the tithi range raises."""
    days = _shipped_patro(codegen)
    del days["2081-01-01"]
    with pytest.raises(ValueError):
        _patro_tables(codegen, days)


def test_main_returns_nonzero_on_missing_tithi(
    codegen: Any, tmp_path: Path, monkeypatch: Any
) -> None:
    """The generator exits non-zero when a day inside the tithi range has no tithi."""
    copied = tmp_path / "patro"
    shutil.copytree(codegen.PATRO_DIR, copied)
    path = copied / "2081.json"
    raw = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    del raw["days"]["2081-01-01"]
    path.write_text(json.dumps(raw), encoding="utf-8")
    monkeypatch.setattr(codegen, "PATRO_DIR", copied)
    assert codegen.main([]) == 1


def test_generate_patro_is_deterministic(codegen: Any) -> None:
    """The rendered patro module is byte for byte stable."""
    tables = _patro_tables(codegen)
    assert codegen.generate_patro_py(tables) == codegen.generate_patro_py(tables)


def test_generated_patro_matches_file(codegen: Any) -> None:
    """The on-disk ``_tables.py`` matches what the generator would write."""
    tables = _patro_tables(codegen)
    assert codegen.PATRO_TABLES_PY.read_text(encoding="utf-8") == codegen.generate_patro_py(tables)


def test_source_text_escapes_invisible_characters(codegen: Any) -> None:
    r"""An invisible character is emitted as a ``\N{...}`` escape, not raw."""
    assert codegen.source_text(f"a{_INVISIBLE}b") == "'a\\N{ZERO WIDTH NON-JOINER}b'"


def test_patro_generation_escapes_invisible_characters(codegen: Any) -> None:
    """A generated name never contains a raw invisible character.

    The source rule: the raw joiner must become an escape.
    """
    days = _shipped_patro(codegen)
    days["2081-01-01"]["tithi"]["en"] += _INVISIBLE
    source = codegen.generate_patro_py(_patro_tables(codegen, days))
    assert "\\N{ZERO WIDTH NON-JOINER}" in source
    assert _INVISIBLE not in source

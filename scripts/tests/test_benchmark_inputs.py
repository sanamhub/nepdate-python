"""The benchmark inputs are the 64 dates of BENCHMARK.md and match the generated tables."""

from __future__ import annotations

from typing import Any

from nepdate import NepaliDate
from nepdate_patro import coverage

INPUT_COUNT = 64


def test_core_literals_match_the_generated_tables(benchmark_inputs: Any) -> None:
    """The committed literals and the recomputed core dates agree."""
    assert len(benchmark_inputs.DATES_BS) == INPUT_COUNT
    assert benchmark_inputs.computed_bs() == benchmark_inputs.DATES_BS
    assert benchmark_inputs.computed_ad() == benchmark_inputs.DATES_AD
    assert benchmark_inputs.computed_text() == benchmark_inputs.DATES_TEXT


def test_core_dates_round_trip(benchmark_inputs: Any) -> None:
    """Every literal BS date converts to its committed AD date and text form."""
    for bs, ad, text in zip(
        benchmark_inputs.DATES_BS,
        benchmark_inputs.DATES_AD,
        benchmark_inputs.DATES_TEXT,
        strict=True,
    ):
        assert NepaliDate(*bs).to_date() == ad
        assert f"{bs[0]:04d}/{bs[1]:02d}/{bs[2]:02d}" == text


def test_core_range_is_bs_2000_to_2090(benchmark_inputs: Any) -> None:
    """The first and last core dates follow the BENCHMARK §2 serial step."""
    assert benchmark_inputs.DATES_BS[0] == (2000, 1, 1)
    assert benchmark_inputs.DATES_BS[-1] == (2090, 11, 24)


def test_patro_literals_match_the_coverage(benchmark_inputs: Any) -> None:
    """The committed patro dates and the recomputed coverage dates agree."""
    assert len(benchmark_inputs.DATES_PATRO) == INPUT_COUNT
    assert benchmark_inputs.computed_patro() == benchmark_inputs.DATES_PATRO
    assert benchmark_inputs.DATES_PATRO[0] == (2077, 1, 1)
    assert benchmark_inputs.DATES_PATRO[-1] == (2084, 7, 30)
    inside = coverage()
    for bs in benchmark_inputs.DATES_PATRO:
        assert NepaliDate(*bs) in inside


def test_literal_check_negative_control(benchmark_inputs: Any) -> None:
    """A different end date changes the recomputed list, so the comparison can fail."""
    other = benchmark_inputs._sample((2001, 1, 1), (2090, 12, 30))
    assert other != benchmark_inputs.DATES_BS

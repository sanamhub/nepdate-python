"""Tests for the P7 load gate in ``benchmarks/run.py``."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

NOT_QUIET = 3


def _sample(cpu: float, background: float | None = None) -> dict[str, float | int]:
    return {
        "cpu_percent": cpu,
        "cpu2_percent": 0.0,
        "background_percent": cpu if background is None else background,
        "memory_percent": 50.0,
        "processes": 100,
    }


def test_cpu_fields_leave_the_pinned_cpu_out_of_the_background(bench_run: Any) -> None:
    """With only CPU 2 busy, the pinned benchmark alone is not background load."""
    per_cpu = [0.0] * 16
    per_cpu[bench_run.CORE_INDEX] = 100.0
    fields = bench_run._cpu_fields(per_cpu)
    assert fields == {"cpu_percent": 6.2, "cpu2_percent": 100.0, "background_percent": 0.0}


def test_cpu_fields_average_the_other_cpus(bench_run: Any) -> None:
    """The background load is the mean of every CPU except CPU 2."""
    fields = bench_run._cpu_fields([20.0, 40.0, 100.0, 60.0])
    assert fields == {"cpu_percent": 55.0, "cpu2_percent": 100.0, "background_percent": 40.0}


def test_quiet_run_with_a_busy_pinned_cpu_is_not_loaded(bench_run: Any) -> None:
    """A run whose own CPU pushes the all-CPU load up is still quiet."""
    samples = [_sample(cpu=17.0, background=8.0), _sample(cpu=16.0, background=7.5)]
    assert not bench_run._is_loaded(_sample(cpu=3.0), samples)


def test_load_before_the_run_marks_the_row_loaded(bench_run: Any) -> None:
    """The all-CPU load before the run decides on its own."""
    assert bench_run._is_loaded(_sample(cpu=bench_run.LOAD_LIMIT), [])


def test_background_spike_during_the_run_marks_the_row_loaded(bench_run: Any) -> None:
    """One background sample at the limit marks the row loaded."""
    samples = [_sample(cpu=10.0, background=5.0), _sample(cpu=20.0, background=15.0)]
    assert bench_run._is_loaded(_sample(cpu=3.0), samples)


def test_record_attempt_creates_then_appends(bench_run: Any, tmp_path: Path) -> None:
    """``quiet.json`` is created once and then appended to."""
    bench_run._record_attempt(tmp_path, _sample(cpu=40.0))
    bench_run._record_attempt(tmp_path, _sample(cpu=4.0))
    data = json.loads((tmp_path / "quiet.json").read_text(encoding="utf-8"))
    assert data["limit"] == bench_run.LOAD_LIMIT
    assert [attempt["quiet"] for attempt in data["attempts"]] == [False, True]
    assert all("at" in attempt for attempt in data["attempts"])


@pytest.fixture
def gated(bench_run: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Point ``run.py`` at a temporary root and make importing the benchmarks fail loudly."""
    monkeypatch.setattr(bench_run, "ROOT", tmp_path)
    monkeypatch.setitem(sys.modules, "benchmarks", None)
    monkeypatch.setitem(sys.modules, "benchmarks.bench", None)
    return bench_run


def _attempts(root: Path, day: str) -> list[dict[str, object]]:
    path = root / "benchmarks" / "results" / day / "quiet.json"
    attempts: list[dict[str, object]] = json.loads(path.read_text(encoding="utf-8"))["attempts"]
    return attempts


@pytest.mark.parametrize(("cpu", "code"), [(40.0, 1), (4.0, 0)])
def test_check_load_exits_on_the_sample_and_records_it(
    gated: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cpu: float, code: int
) -> None:
    """``--check-load`` exits 1 when loaded, 0 when quiet, and records the sample."""
    monkeypatch.setattr(gated, "_load_sample", lambda: _sample(cpu=cpu))
    assert gated.main(["--date", "d", "--check-load"]) == code
    assert _attempts(tmp_path, "d")[-1]["cpu_percent"] == cpu


def test_loaded_machine_stops_before_importing_the_benchmarks(
    gated: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A loaded machine exits 3 without importing the benchmarks or a competitor."""
    monkeypatch.setattr(gated, "_load_sample", lambda: _sample(cpu=40.0))
    assert gated.main(["--date", "d"]) == NOT_QUIET
    assert _attempts(tmp_path, "d")[-1]["quiet"] is False


def test_allow_loaded_goes_on_to_the_benchmarks(
    gated: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Negative control: past the gate, ``run.py`` imports the benchmarks."""
    monkeypatch.setattr(gated, "_load_sample", lambda: _sample(cpu=40.0))
    with pytest.raises(ImportError):
        gated.main(["--date", "d", "--allow-loaded"])

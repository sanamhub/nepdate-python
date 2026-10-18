"""The 183-day patro freshness gate is tested at the boundary and on a temporary data tree."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from nepdate import NepaliDate


def _write_patro(root: Path, days: dict[str, object]) -> None:
    """Write one patro JSON file below ``root``.

    Args:
        root: The temporary repository root.
        days: The ``days`` object.
    """
    folder = root / "shared" / "data" / "patro"
    folder.mkdir(parents=True)
    (folder / "2081.json").write_text(
        json.dumps({"schema": 1, "year": 2081, "days": days}), encoding="utf-8"
    )


def test_exactly_183_days_passes(data_status: Any) -> None:
    """The boundary is inclusive: 183 days left is not a failure."""
    ranges = data_status.coverage(data_status.ROOT)
    last = NepaliDate.parse(ranges["holidays"][1]).to_date()
    report = data_status.diagnose(data_status.ROOT, last - timedelta(days=183))
    assert report.ok


def test_182_days_fails(data_status: Any) -> None:
    """One day short of 183 fails and names the public holiday range."""
    ranges = data_status.coverage(data_status.ROOT)
    last = NepaliDate.parse(ranges["holidays"][1]).to_date()
    report = data_status.diagnose(data_status.ROOT, last - timedelta(days=182))
    assert not report.ok
    assert any("public holiday" in failure for failure in report.failures)
    assert any("182 days" in failure for failure in report.failures)


def test_short_tithi_only_warns(data_status: Any) -> None:
    """A tithi range shorter than the gate does not fail the release."""
    ranges = data_status.coverage(data_status.ROOT)
    last = NepaliDate.parse(ranges["tithi"][1]).to_date()
    report = data_status.diagnose(data_status.ROOT, last - timedelta(days=10))
    assert report.ok
    assert any(warning.startswith("tithi") for warning in report.warnings)


def test_missing_holidays_fail(data_status: Any, tmp_path: Path) -> None:
    """A data tree with no public holiday fails, even when other kinds exist."""
    _write_patro(tmp_path, {"2081-01-01": {"tithi": {"np": "x", "en": "x"}}})
    report = data_status.diagnose(tmp_path, date(2026, 10, 18))
    assert not report.ok
    assert any("missing" in failure for failure in report.failures)


def test_missing_directory_is_an_error(data_status: Any, tmp_path: Path) -> None:
    """An empty root is a read error, not a pass."""
    with pytest.raises(data_status.DataError):
        data_status.coverage(tmp_path)


def test_cli_boundary(data_status: Any) -> None:
    """The command exits 0 at 183 days and 1 at 182."""
    ranges = data_status.coverage(data_status.ROOT)
    last = NepaliDate.parse(ranges["holidays"][1]).to_date()
    at_183 = (last - timedelta(days=183)).isoformat()
    at_182 = (last - timedelta(days=182)).isoformat()
    assert data_status.main(["--today", at_183]) == 0
    assert data_status.main(["--today", at_182]) == 1


def test_cli_rejects_a_bad_date(data_status: Any) -> None:
    """``--today`` must be a real ISO date."""
    with pytest.raises(SystemExit):
        data_status.main(["--today", "2026-02-30"])

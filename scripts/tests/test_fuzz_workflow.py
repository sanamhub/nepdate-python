"""The fuzz workflow keeps its schedule, budget, pins and release gate."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "fuzz.yml"
RELEASE = ROOT / ".github" / "workflows" / "release.yml"
SHA = re.compile(r"@[0-9a-f]{40}$")
BUDGET = "-max_total_time=300"
PUBLISH_JOBS = 2


def _workflow() -> str:
    """Return the weekly fuzz workflow text."""
    return WORKFLOW.read_text(encoding="utf-8")


def test_weekly_workflow_runs_every_target() -> None:
    """The weekly workflow is scheduled, has no pull-request trigger, and runs three targets."""
    text = _workflow()
    assert 'cron: "0 4 * * 1"' in text
    assert "workflow_dispatch:" in text
    assert "pull_request" not in text
    assert "target: [parse, parse_lenient, format]" in text
    assert BUDGET in text
    assert "contents: read" in text


def test_workflow_actions_are_pinned() -> None:
    """Every action in the fuzz and release workflows uses a full commit SHA."""
    for path in (WORKFLOW, RELEASE):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.search(r"\buses:\s*(\S+)", line)
            if match is not None and not match.group(1).startswith("./"):
                assert SHA.search(match.group(1)), f"{path.name}: {line.strip()}"


def test_release_runs_fuzz_before_publish() -> None:
    """The release has a fuzz job with the same targets, and both publish jobs need it."""
    text = RELEASE.read_text(encoding="utf-8")
    assert "  fuzz:" in text
    assert "target: [parse, parse_lenient, format]" in text
    assert BUDGET in text
    assert "needs: [preflight, build, mutation, fuzz]" in text
    assert text.count("needs: [preflight, build, mutation, fuzz]") == PUBLISH_JOBS


def test_crash_inputs_are_uploaded_on_failure() -> None:
    """Both fuzz jobs keep the crash input when a target fails."""
    for path in (WORKFLOW, RELEASE):
        text = path.read_text(encoding="utf-8")
        assert "if: failure()" in text, path.name
        assert "name: fuzz-artifacts-${{ matrix.target }}" in text, path.name

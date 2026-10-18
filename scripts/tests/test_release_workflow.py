"""The release workflow keeps its permissions, pins and shell inputs in the right places."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
SHA = re.compile(r"@[0-9a-f]{40}$")
EXPRESSION = "${{"


def _indent(line: str) -> int:
    """Return the number of leading spaces.

    Args:
        line: One line of YAML.

    Returns:
        The indentation width.
    """
    return len(line) - len(line.lstrip(" "))


def _block(lines: list[str], start: int) -> list[str]:
    """Return a mapping block starting at ``start``.

    Args:
        lines: The workflow lines.
        start: The line index of the mapping key.

    Returns:
        The key line and its more-indented lines.
    """
    base = _indent(lines[start])
    block = [lines[start]]
    for line in lines[start + 1 :]:
        if line.strip() and _indent(line) <= base:
            break
        block.append(line)
    return block


def _job(lines: list[str], name: str) -> list[str]:
    """Return one job block by name.

    Args:
        lines: The workflow lines.
        name: The job key below ``jobs:``.

    Returns:
        The job's lines, or an empty list when it is absent.
    """
    for index, line in enumerate(lines):
        if line == f"  {name}:":
            return _block(lines, index)
    return []


def problems(text: str) -> list[str]:  # noqa: PLR0912, PLR0915 - one pass, one message per rule
    """Check the workflow rules that a review keeps missing.

    Args:
        text: The release workflow text.

    Returns:
        One message per violation.
    """
    lines = text.splitlines()
    found: list[str] = []
    top = ""
    for index, line in enumerate(lines):
        if line == "permissions:":
            top = "\n".join(_block(lines, index))
            break
    if "contents: read" not in top:
        found.append("default permissions must be contents: read")
    for index, line in enumerate(lines):
        match = re.search(r"\brun:\s*(.*)$", line)
        if match is None:
            continue
        base = _indent(line)
        if EXPRESSION in match.group(1):
            found.append(f"line {index + 1}: expression inside run")
        if match.group(1).strip() == "|":
            for inner in lines[index + 1 :]:
                if inner.strip() and _indent(inner) <= base:
                    break
                if EXPRESSION in inner:
                    found.append(f"line {index + 1}: expression inside run")
                    break
    for index, line in enumerate(lines):
        match = re.search(r"\buses:\s*(\S+)", line)
        if match and not match.group(1).startswith("./") and not SHA.search(match.group(1)):
            found.append(f"line {index + 1}: action is not pinned by SHA")
    build = "\n".join(_job(lines, "build"))
    if "scripts/ci.py build-release" not in build:
        found.append("the build job must stage the shared data before uv build")
    publish = "\n".join(_job(lines, "publish"))
    if "environment: production" not in publish:
        found.append("publish must use the production environment")
    if "contents: write" not in publish or "id-token: write" not in publish:
        found.append("publish needs contents: write and id-token: write")
    if "github.event_name == 'push'" not in publish or "refs/tags/v" not in publish:
        found.append("publish must run only on a tag push")
    if "fetch-depth: 0" not in publish:
        found.append("publish checkout must fetch full history")
    if "git fetch --no-tags origin main" not in publish:
        found.append("publish must fetch origin/main")
    check_at = publish.find("merge-base --is-ancestor")
    if check_at < 0:
        found.append("publish must verify the tag is on origin/main")
    upload_at = publish.find("gh-action-pypi-publish")
    if check_at >= 0 and upload_at >= 0 and check_at > upload_at:
        found.append("publish must check main before uploading")
    if "COMMIT_SHA: ${{ github.sha }}" not in publish:
        found.append("publish must pass github.sha through env")
    testpypi = "\n".join(_job(lines, "publish-testpypi"))
    if "environment: testpypi" not in testpypi:
        found.append("TestPyPI must use the testpypi environment")
    if "id-token: write" not in testpypi or "contents: write" in testpypi:
        found.append("TestPyPI needs id-token: write and not contents: write")
    if "default: true" not in text:
        found.append("the dry-run input must default to true")
    return found


def test_release_workflow_rules() -> None:
    """The shipped workflow satisfies every rule."""
    assert problems(WORKFLOW.read_text(encoding="utf-8")) == []


def test_workflow_rules_negative_control() -> None:
    """A write default, an unpinned action, an expression in run and no main check are reported."""
    bad = """\
on:
  workflow_dispatch:
permissions:
  contents: write
jobs:
  publish:
    if: github.event_name == 'workflow_dispatch'
    environment: production
    permissions:
      contents: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - run: echo "${{ inputs.version }}"
      - uses: pypa/gh-action-pypi-publish@v1
"""
    found = problems(bad)
    assert any("default permissions" in message for message in found)
    assert any("not pinned" in message for message in found)
    assert any("expression inside run" in message for message in found)
    assert any("tag push" in message for message in found)
    assert any("verify the tag is on origin/main" in message for message in found)
    assert any("stage the shared data" in message for message in found)

"""The release workflow keeps its permissions, pins and shell inputs in the right places."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
SHA = re.compile(r"@[0-9a-f]{40}$")
EXPRESSION = "${{"
VERIFY_JOBS = (
    ("verify", "publish", "https://pypi.org/simple/"),
    ("verify-testpypi", "publish-testpypi", "https://test.pypi.org/simple/"),
)


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


def _needs(block: str) -> set[str]:
    """Return the jobs in a job block's ``needs`` list.

    Args:
        block: One job block.

    Returns:
        The job names, or an empty set when the block has no inline needs list.
    """
    match = re.search(r"^    needs:\s*\[(.*?)\]$", block, re.MULTILINE)
    if match is None:
        return set()
    return {part.strip() for part in match.group(1).split(",")}


def verify_problems(text: str) -> list[str]:  # noqa: PLR0912 - one branch per rule
    """Check the two post-publish jobs and the index each one uses.

    Args:
        text: The release workflow text.

    Returns:
        One message per missing or wrong rule.
    """
    lines = text.splitlines()
    found: list[str] = []
    for name, publisher, index in VERIFY_JOBS:
        block = "\n".join(_job(lines, name))
        if not block:
            found.append(f"missing {name} job")
            continue
        needs = _needs(block)
        if publisher not in needs:
            found.append(f"{name} must need {publisher}")
        if "preflight" not in needs:
            found.append(f"{name} must need preflight for the version")
        if "    permissions:\n      contents: read" not in block:
            found.append(f"{name} must set contents: read")
        if "id-token" in block:
            found.append(f"{name} must not request id-token")
        if "runs-on: ubuntu-latest" not in block:
            found.append(f"{name} must run on ubuntu-latest")
        if "astral-sh/setup-uv@" not in block:
            found.append(f"{name} must install uv")
        if index not in block:
            found.append(f"{name} must use {index}")
        if "VERSION: ${{ needs.preflight.outputs.version }}" not in block:
            found.append(f"{name} must read the preflight version")
        if "uv pip install" not in block or "SECONDS + 600" not in block or "sleep" not in block:
            found.append(f"{name} must retry the install for up to 10 minutes")
        if "nepdate-core==$VERSION" not in block or "nepdate-patro==$VERSION" not in block:
            found.append(f"{name} must install both exact versions")
        if "NepaliDate(2080, 5, 15)" not in block:
            found.append(f"{name} must run the README quick start")
        if "from nepdate_patro import info" not in block or "info(d)" not in block:
            found.append(f"{name} must call nepdate_patro.info")
    return found


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
        found.append("the build job must build with scripts/ci.py build-release")
    if 'release-rehearsal "$VERSION" --dist dist' not in build:
        found.append("the build job must check the built files it uploads")
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
    found.extend(verify_problems(text))
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
    assert any("build-release" in message for message in found)
    assert any("check the built files" in message for message in found)


def _verify_block(text: str, name: str = "verify") -> str:
    """Return one verify job as text.

    Args:
        text: The release workflow text.
        name: The job name.

    Returns:
        The job block without its trailing newline.
    """
    return "\n".join(_job(text.splitlines(), name))


def test_verify_jobs_follow_the_publishers() -> None:
    """Both verify jobs exist and use the index that their publisher wrote to."""
    assert verify_problems(WORKFLOW.read_text(encoding="utf-8")) == []


def test_verify_job_missing_is_reported() -> None:
    """A workflow without the PyPI verify job fails the check."""
    text = WORKFLOW.read_text(encoding="utf-8")
    block = _verify_block(text)
    assert block
    found = verify_problems(text.replace(block + "\n", "", 1))
    assert "missing verify job" in found


def test_verify_job_wrong_needs_is_reported() -> None:
    """A verify job that does not follow publish fails the check."""
    text = WORKFLOW.read_text(encoding="utf-8")
    block = _verify_block(text)
    bad_block = block.replace("needs: [preflight, publish]", "needs: [preflight]", 1)
    assert bad_block != block
    found = verify_problems(text.replace(block, bad_block, 1))
    assert "verify must need publish" in found


def test_verify_job_id_token_is_reported() -> None:
    """A verify job with an upload permission fails the check."""
    text = WORKFLOW.read_text(encoding="utf-8")
    block = _verify_block(text)
    bad_block = block.replace(
        "      contents: read",
        "      contents: read\n      id-token: write",
        1,
    )
    assert bad_block != block
    found = verify_problems(text.replace(block, bad_block, 1))
    assert "verify must not request id-token" in found

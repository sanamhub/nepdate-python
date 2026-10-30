"""The release workflow keeps its permissions, pins and shell inputs in the right places."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
VERIFY_WORKFLOW = ROOT / ".github" / "workflows" / "verify-published.yml"
SHA = re.compile(r"@[0-9a-f]{40}$")
EXPRESSION = "${{"
VERIFY_JOBS = (
    ("verify", "publish-patro", "https://pypi.org/simple/"),
    ("verify-testpypi", "publish-patro-testpypi", "https://test.pypi.org/simple/"),
)
# Each upload job, its environment and the one dist directory it uploads. PyPI matches a trusted
# publisher on repository, workflow and environment, so every distribution needs its own
# environment: a shared one let the patro's pending publisher claim the core upload on TestPyPI.
PUBLISH_JOBS = (
    ("publish", "production", "dist/core/"),
    ("publish-patro", "production-patro", "dist/patro/"),
    ("publish-testpypi", "testpypi", "dist/core/"),
    ("publish-patro-testpypi", "testpypi-patro", "dist/patro/"),
)


def publisher_problems(text: str) -> list[str]:
    """Check that each distribution uploads from its own job and environment.

    Args:
        text: The release workflow text.

    Returns:
        One message per missing or wrong rule.
    """
    lines = text.splitlines()
    found: list[str] = []
    seen: dict[str, str] = {}
    for name, environment, directory in PUBLISH_JOBS:
        block = "\n".join(_job(lines, name))
        if not block:
            found.append(f"missing {name} job")
            continue
        match = re.search(r"^    environment:\s*(\S+)$", block, re.MULTILINE)
        actual = match.group(1) if match else ""
        if actual != environment:
            found.append(f"{name} must use the {environment} environment")
        if actual in seen:
            found.append(f"{name} shares the {actual} environment with {seen[actual]}")
        seen[actual] = name
        uploads = re.findall(r"packages-dir:\s*(\S+)", block)
        if uploads != [directory]:
            found.append(f"{name} must upload only {directory}")
        if "id-token: write" not in block or "contents: write" in block:
            found.append(f"{name} needs id-token: write and not contents: write")
    return found


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


def verify_problems(text: str) -> list[str]:
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
        if "uses: ./.github/workflows/verify-published.yml" not in block:
            found.append(f"{name} must call verify-published.yml")
        if f"index-url: {index}" not in block:
            found.append(f"{name} must use {index}")
        if "version: ${{ needs.preflight.outputs.pypi-version }}" not in block:
            found.append(f"{name} must pass the PyPI spelling of the preflight version")
    return found


def verify_workflow_problems(text: str) -> list[str]:
    """Check the reusable post-upload workflow.

    Args:
        text: The ``verify-published.yml`` text.

    Returns:
        One message per missing or wrong rule.
    """
    found: list[str] = []
    if "workflow_call:" not in text or "workflow_dispatch:" not in text:
        found.append("verify-published must be callable and dispatchable")
    if "permissions:\n  contents: read" not in text or "id-token" in text:
        found.append("verify-published must be read-only")
    for os_name in ("ubuntu-latest", "macos-latest", "windows-latest"):
        if os_name not in text:
            found.append(f"verify-published must run on {os_name}")
    if 'python: ["3.11", "3.14"]' not in text:
        found.append("verify-published must run the oldest and newest Python")
    if "scripts/verify_published.py" not in text or "--wait-seconds" not in text:
        found.append("verify-published must run scripts/verify_published.py with a wait")
    if "INPUT_VERSION: ${{ inputs.version }}" not in text:
        found.append("verify-published must pass the input version through env")
    if "VERSION: ${{ needs.resolve.outputs.version }}" not in text:
        found.append("verify-published must pass the resolved version through env")
    for cron in ('cron: "41 7 * * 1"', 'cron: "37 3 * * *"'):
        if cron not in text:
            found.append("verify-published must keep the weekly and daily schedules")
    return found


def problems(text: str) -> list[str]:  # noqa: PLR0912, PLR0915 - one pass, one message per rule
    """Check the workflow rules that are easy to miss.

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
    for job in ("publish", "publish-patro"):
        publish = "\n".join(_job(lines, job))
        if "id-token: write" not in publish or "contents: write" in publish:
            found.append(f"{job} needs id-token: write and not contents: write")
        if "action-gh-release" in publish:
            found.append(
                f"{job} must not create the GitHub Release; github-release does after verify"
            )
        if "github.event_name == 'push'" not in publish or "refs/tags/v" not in publish:
            found.append(f"{job} must run only on a tag push")
        if "fetch-depth: 0" not in publish:
            found.append(f"{job} checkout must fetch full history")
        if "git fetch --no-tags origin main" not in publish:
            found.append(f"{job} must fetch origin/main")
        check_at = publish.find("merge-base --is-ancestor")
        if check_at < 0:
            found.append(f"{job} must verify the tag is on origin/main")
        upload_at = publish.find("gh-action-pypi-publish")
        if check_at >= 0 and upload_at >= 0 and check_at > upload_at:
            found.append(f"{job} must check main before uploading")
        if "COMMIT_SHA: ${{ github.sha }}" not in publish:
            found.append(f"{job} must pass github.sha through env")
    if "publish" not in _needs("\n".join(_job(lines, "publish-patro"))):
        found.append("publish-patro must need publish, so the core exists first")
    if "publish-testpypi" not in _needs("\n".join(_job(lines, "publish-patro-testpypi"))):
        found.append("publish-patro-testpypi must need publish-testpypi")
    found.extend(publisher_problems(text))
    if "default: true" not in text:
        found.append("the dry-run input must default to true")
    preflight = "\n".join(_job(lines, "preflight"))
    if "pypi-version: ${{ steps.pypi.outputs.pypi-version }}" not in preflight:
        found.append("preflight must output the PyPI spelling of the version")
    found.extend(verify_problems(text))
    found.extend(github_release_problems(text))
    return found


def github_release_problems(text: str) -> list[str]:
    """Check that the GitHub Release is created only after the PyPI verify job.

    Args:
        text: The release workflow text.

    Returns:
        One message per missing or wrong rule.
    """
    lines = text.splitlines()
    block = "\n".join(_job(lines, "github-release"))
    if not block:
        return ["missing github-release job"]
    found: list[str] = []
    if "verify" not in _needs(block):
        found.append("github-release must need verify")
    if "    permissions:\n      contents: write" not in block:
        found.append("github-release must set contents: write")
    if "id-token" in block:
        found.append("github-release must not request id-token")
    if "softprops/action-gh-release@" not in block:
        found.append("github-release must create the release")
    if "prerelease: ${{ needs.preflight.outputs.prerelease == 'true' }}" not in block:
        found.append("github-release must mark a beta or rc tag as a pre-release")
    for name in ("verify", "verify-testpypi"):
        if "action-gh-release" in "\n".join(_job(lines, name)):
            found.append(f"{name} must not create the GitHub Release")
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
    bad_block = block.replace("needs: [preflight, publish-patro]", "needs: [preflight]", 1)
    assert bad_block != block
    found = verify_problems(text.replace(block, bad_block, 1))
    assert "verify must need publish-patro" in found


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


def test_release_page_after_verify() -> None:
    """The shipped workflow creates the GitHub Release only after verify."""
    assert github_release_problems(WORKFLOW.read_text(encoding="utf-8")) == []


def test_release_page_before_verify_is_reported() -> None:
    """A GitHub Release job that does not wait for verify fails the check."""
    text = WORKFLOW.read_text(encoding="utf-8")
    block = _verify_block(text, "github-release")
    bad_block = block.replace("needs: [preflight, verify]", "needs: [preflight, publish]", 1)
    assert bad_block != block
    found = problems(text.replace(block, bad_block, 1))
    assert "github-release must need verify" in found


def test_release_page_in_publish_is_reported() -> None:
    """Creating the GitHub Release in the publish job again fails the check."""
    text = WORKFLOW.read_text(encoding="utf-8")
    block = _verify_block(text, "publish")
    write_block = block.replace(
        "      contents: read\n      id-token", "      contents: write\n      id-token", 1
    )
    assert write_block != block
    bad_block = write_block + (
        "\n      - uses: softprops/action-gh-release@3bb12739c298aeb8a4eeaf626c5b8d85266b0e65"
    )
    found = problems(text.replace(block, bad_block, 1))
    assert "publish needs id-token: write and not contents: write" in found
    assert any("publish must not create the GitHub Release" in message for message in found)


def test_verify_jobs_run_the_same_steps() -> None:
    """The two verify jobs differ only in name, needs and index, so the copy cannot drift."""
    text = WORKFLOW.read_text(encoding="utf-8")
    pypi = _verify_block(text, "verify")
    testpypi = _verify_block(text, "verify-testpypi")
    normalised = (
        testpypi.replace("  verify-testpypi:", "  verify:", 1)
        .replace("name: verify from TestPyPI", "name: verify from PyPI", 1)
        .replace("[preflight, publish-patro-testpypi]", "[preflight, publish-patro]", 1)
        .replace("https://test.pypi.org/simple/", "https://pypi.org/simple/", 1)
    )
    testpypi_only = (
        "      # tzdata (Windows) and pip's own build tools are not reliably on TestPyPI.\n"
        "      extra-index-url: https://pypi.org/simple/"
    )
    assert normalised.replace("\n" + testpypi_only, "").rstrip() == pypi.rstrip()


def test_verify_workflow_rules() -> None:
    """The reusable post-upload workflow satisfies every rule."""
    text = VERIFY_WORKFLOW.read_text(encoding="utf-8")
    assert verify_workflow_problems(text) == []
    assert [p for p in problems(text) if "expression inside run" in p or "not pinned" in p] == []


def test_verify_workflow_negative_control() -> None:
    """Dropping Windows, the newest Python or the wait is reported."""
    text = VERIFY_WORKFLOW.read_text(encoding="utf-8")
    bad = (
        text.replace("windows-latest", "")
        .replace('"3.11", "3.14"', '"3.11"')
        .replace("--wait-seconds", "--no-wait")
    )
    found = verify_workflow_problems(bad)
    assert "verify-published must run on windows-latest" in found
    assert "verify-published must run the oldest and newest Python" in found
    assert "verify-published must run scripts/verify_published.py with a wait" in found


def test_publishers_have_their_own_environments() -> None:
    """The shipped workflow uploads each distribution from its own job and environment."""
    assert publisher_problems(WORKFLOW.read_text(encoding="utf-8")) == []


def test_shared_publisher_environment_is_reported() -> None:
    """Uploading the patro from the core's environment, as the first beta dry run did, fails."""
    text = WORKFLOW.read_text(encoding="utf-8")
    bad = text.replace("environment: testpypi-patro", "environment: testpypi", 1)
    assert bad != text
    found = publisher_problems(bad)
    assert "publish-patro-testpypi must use the testpypi-patro environment" in found
    assert any("shares the testpypi environment" in message for message in found)


def test_two_uploads_in_one_job_are_reported() -> None:
    """Moving the patro upload back into the core job fails the check."""
    text = WORKFLOW.read_text(encoding="utf-8")
    block = _verify_block(text, "publish")
    bad_block = block + (
        "\n      - name: Publish nepdate-patro"
        "\n        uses: pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33"
        "\n        with:"
        "\n          packages-dir: dist/patro/"
    )
    found = publisher_problems(text.replace(block, bad_block, 1))
    assert "publish must upload only dist/core/" in found


def test_release_without_prerelease_flag_is_reported() -> None:
    """A GitHub Release that never sets prerelease would show a beta as the latest release."""
    text = WORKFLOW.read_text(encoding="utf-8")
    bad = text.replace("prerelease: ${{ needs.preflight.outputs.prerelease == 'true' }}", "")
    assert "github-release must mark a beta or rc tag as a pre-release" in problems(bad)

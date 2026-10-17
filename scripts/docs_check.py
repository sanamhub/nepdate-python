"""Check the user-facing documentation for the house rules.

The gate covers the files a reader meets before the source: the README, changelog, contribution
guide, security policy and the top-level pages in ``docs/``. Plans and ADRs keep their task IDs,
so they are not part of this check.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
FIXED_FILES = ("README.md", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md")
TASK_ID = re.compile(r"\bP[0-9]+-[0-9]{2}\b")
LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SCHEMES = ("http://", "https://", "mailto:")


def _targets(root: Path) -> list[Path]:
    """Return the files the documentation gate checks.

    Args:
        root: The repository root.

    Returns:
        The fixed files that exist, then every top-level ``docs/*.md`` file, sorted by path.
    """
    files = [root / name for name in FIXED_FILES if (root / name).is_file()]
    files.extend(sorted((root / "docs").glob("*.md")))
    return files


def _link_target(raw: str) -> str:
    """Extract the path from a Markdown link target.

    Args:
        raw: The text inside the parentheses, for example ``<docs/API.md>`` or ``x.md "title"``.

    Returns:
        The path without angle brackets, title or fragment.
    """
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split()[0] if target else ""
    return unquote(target.split("#", 1)[0])


def problems(root: Path = ROOT) -> list[str]:
    """Return one message per documentation rule violation.

    Args:
        root: The repository root to check. Tests pass a temporary directory.

    Returns:
        Messages of the form ``path:line: reason``. An empty list means the docs pass.
    """
    found: list[str] = []
    for path in _targets(root):
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            location = f"{path.relative_to(root).as_posix()}:{number}"
            if "\u2014" in line:
                found.append(f"{location}: em dash")
            if TASK_ID.search(line):
                found.append(f"{location}: task ID")
            for match in LINK.finditer(line):
                target = _link_target(match.group(1))
                if not target or target.startswith("#") or target.startswith(SCHEMES):
                    continue
                resolved = (path.parent / target).resolve()
                if not resolved.exists():
                    found.append(f"{location}: link does not resolve: {target}")
    return found


def main(argv: list[str] | None = None) -> int:
    """Run the documentation check.

    Args:
        argv: Command line arguments; none are accepted.

    Returns:
        0 when the docs pass, 1 when a rule is broken, 2 on an unknown argument.
    """
    if argv is None:
        argv = sys.argv[1:]
    if argv:
        print(f"docs: unknown arguments {argv}", file=sys.stderr)
        return 2
    found = problems()
    for message in found:
        print(f"docs: {message}", file=sys.stderr)
    if found:
        return 1
    print("docs: user-facing docs pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

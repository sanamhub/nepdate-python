"""Run ``scripts/ci.py`` on every Python version in the CI workflow matrix.

The version list is read from ``.github/workflows/ci.yml``, so the local run cannot drift from the
matrix GitHub would use. Each version gets its own project environment, Python installation and uv
cache under one directory on the D drive. A version that uv cannot provide is skipped and is never
counted as passed.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
DEFAULT_JOBS = 2
MAX_JOBS = 4
TEST_JOB = re.compile(r"^  ([A-Za-z0-9_-]+):\s*$")
PYTHON = re.compile(r"""python:\s*["']([^"']+)["']""")


class MatrixError(Exception):
    """Raised when the workflow has no readable test matrix."""


class RunResult:
    """One version's outcome.

    Attributes:
        version: The Python request, for example ``3.14t``.
        status: ``passed``, ``failed`` or ``skipped``.
        detail: The last output line, or the reason the version was skipped.
        log: The log path when the version ran.
    """

    __slots__ = ("detail", "log", "status", "version")

    def __init__(self, version: str, status: str, detail: str, log: Path | None = None) -> None:
        """Store one outcome.

        Args:
            version: The Python request.
            status: ``passed``, ``failed`` or ``skipped``.
            detail: The last output line or the skip reason.
            log: The log path when the version ran.
        """
        self.version = version
        self.status = status
        self.detail = detail
        self.log = log


def default_cache_root() -> Path:
    r"""Return the cache root for this platform.

    Returns:
        ``D:\\devcache\\p10`` on Windows, ``/mnt/d/devcache/p10`` elsewhere.
    """
    if os.name == "nt":
        return Path(r"D:\devcache\p10")
    return Path("/mnt/d/devcache/p10")


def matrix_versions(workflow: Path = DEFAULT_WORKFLOW) -> list[str]:
    """Read the unique Python versions from the ``test`` job's matrix.

    Args:
        workflow: The workflow file.

    Returns:
        The versions in file order, without duplicates.

    Raises:
        MatrixError: The file has no ``test`` job or no matrix Python entry.
        OSError: The file cannot be read.
    """
    text = workflow.read_text(encoding="utf-8")
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line == "  test:"), None)
    if start is None:
        raise MatrixError(f"{workflow}: no test job")
    versions: list[str] = []
    for line in lines[start + 1 :]:
        if TEST_JOB.match(line):
            break
        match = PYTHON.search(line)
        if match is not None and match.group(1) not in versions:
            versions.append(match.group(1))
    if not versions:
        raise MatrixError(f"{workflow}: the test job has no matrix Python versions")
    return versions


def _slug(version: str) -> str:
    """Return a directory-safe name for one version.

    Args:
        version: The Python request.

    Returns:
        The version with every character outside ``[A-Za-z0-9.]`` replaced by ``_``.
    """
    return re.sub(r"[^A-Za-z0-9.]", "_", version)


def environment(cache_root: Path, version: str, python_dir: Path | None = None) -> dict[str, str]:
    """Build the environment for one version.

    Args:
        cache_root: The root that holds environments, logs and temporary files.
        version: The Python request.
        python_dir: The uv-managed Python installation directory; ``cache_root/python`` by default.

    Returns:
        A copy of the current environment with every uv path pointed below ``cache_root``.
    """
    env = os.environ.copy()
    # A parent `uv run` exports its own VIRTUAL_ENV; the child must use this version's env.
    env.pop("VIRTUAL_ENV", None)
    env.update(
        {
            "UV_PROJECT_ENVIRONMENT": str(cache_root / "envs" / _slug(version)),
            "UV_PYTHON_INSTALL_DIR": str(python_dir or cache_root / "python"),
            "UV_CACHE_DIR": str(cache_root / "uv-cache"),
            "TEMP": str(cache_root / "tmp"),
            "TMP": str(cache_root / "tmp"),
            "UV_LINK_MODE": "copy",
            "UV_PYTHON": version,
            "UV_MANAGED_PYTHON": "1",
            "UV_NO_PROGRESS": "1",
        }
    )
    return env


def _command(version: str) -> list[str]:
    """Return the CI command for one version.

    Args:
        version: The Python request.

    Returns:
        The uv command that runs the gates.
    """
    return [
        "uv",
        "run",
        "--locked",
        "--python",
        version,
        "--managed-python",
        "python",
        "scripts/ci.py",
    ]


def find_python(version: str, env: dict[str, str]) -> str | None:
    """Return the managed interpreter path for one version, or ``None``.

    Args:
        version: The Python request.
        env: The environment built by :func:`environment`.

    Returns:
        The interpreter path when uv can provide it, otherwise ``None``.
    """
    result = subprocess.run(
        [
            "uv",
            "python",
            "find",
            "--no-project",
            "--managed-python",
            "--no-python-downloads",
            version,
        ],
        env=env,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    path = result.stdout.strip()
    if result.returncode != 0 or not path:
        return None
    return path


def _last_line(log: Path) -> str:
    """Return the last non-empty line of a log.

    Args:
        log: The log path.

    Returns:
        The last line, or ``<no output>`` when the log is empty.
    """
    lines = [line.strip() for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
    return lines[-1] if lines else "<no output>"


def run_version(version: str, cache_root: Path, python_dir: Path | None = None) -> RunResult:
    """Run the gates for one version, or skip it when uv has no interpreter.

    Args:
        version: The Python request.
        cache_root: The root for environments, logs, caches and temporary files.
        python_dir: The uv-managed Python installation directory; ``cache_root/python`` by default.

    Returns:
        The outcome, with the log path when the version ran.
    """
    env = environment(cache_root, version, python_dir)
    for name in ("envs", "tmp", "logs", "uv-cache", "python"):
        (cache_root / name).mkdir(parents=True, exist_ok=True)
    if find_python(version, env) is None:
        return RunResult(version, "skipped", f"uv cannot provide Python {version}")

    log = cache_root / "logs" / f"{_slug(version)}.log"
    with log.open("w", encoding="utf-8") as handle:
        result = subprocess.run(
            _command(version),
            cwd=ROOT,
            env=env,
            stdout=handle,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    status = "passed" if result.returncode == 0 else "failed"
    return RunResult(version, status, _last_line(log), log)


def summary_line(results: list[RunResult]) -> str:
    """Build a summary that keeps skipped versions out of the passed count.

    Args:
        results: Every outcome, in any order.

    Returns:
        One line with the ran, passed, failed and skipped counts.
    """
    passed = sum(result.status == "passed" for result in results)
    failed = sum(result.status == "failed" for result in results)
    skipped = [result.version for result in results if result.status == "skipped"]
    ran = passed + failed
    line = f"matrix: {ran} ran, {passed} passed, {failed} failed, {len(skipped)} skipped"
    if skipped:
        line += f" ({', '.join(skipped)})"
    return line


def _tail(log: Path, lines: int = 30) -> str:
    """Return the last lines of a failed log.

    Args:
        log: The log path.
        lines: The number of lines to keep.

    Returns:
        The selected lines, joined by newlines.
    """
    text = [line for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
    return "\n".join(text[-lines:])


def _print_dry_run(versions: list[str], cache_root: Path, python_dir: Path | None) -> None:
    """Print the command and environment for each version.

    Args:
        versions: The matrix versions.
        cache_root: The cache root.
        python_dir: The Python installation directory.
    """
    for version in versions:
        env = environment(cache_root, version, python_dir)
        command = " ".join(_command(version))
        print(f"[{version}] UV_PROJECT_ENVIRONMENT={env['UV_PROJECT_ENVIRONMENT']}")
        print(f"[{version}] {command}")


def run_matrix(
    versions: list[str], cache_root: Path, jobs: int, python_dir: Path | None = None
) -> int:
    """Run every version with at most ``jobs`` processes.

    Args:
        versions: The matrix versions.
        cache_root: The cache root.
        jobs: The maximum number of concurrent gates.
        python_dir: The Python installation directory.

    Returns:
        0 when every run that started passed, 1 when one failed or nothing ran.
    """
    results: list[RunResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        pending = {
            pool.submit(run_version, version, cache_root, python_dir): version
            for version in versions
        }
        for future in concurrent.futures.as_completed(pending):
            result = future.result()
            results.append(result)
            if result.status == "failed":
                print(f"[{result.version}] failed")
                if result.log is not None:
                    print(_tail(result.log))
            elif result.status == "skipped":
                print(f"[{result.version}] skip: {result.detail}")
            else:
                print(f"[{result.version}] {result.detail}")
    results.sort(key=lambda result: versions.index(result.version))
    print(summary_line(results))
    if results and all(result.status == "skipped" for result in results):
        print("matrix: no Python version could run")
        return 1
    return 1 if any(result.status == "failed" for result in results) else 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command line.

    Args:
        argv: The arguments; ``sys.argv[1:]`` by default.

    Returns:
        The parsed arguments.

    Raises:
        SystemExit: The arguments are invalid.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workflow", type=Path, default=DEFAULT_WORKFLOW)
    parser.add_argument("--cache-root", type=Path, default=default_cache_root())
    parser.add_argument("--python-dir", type=Path, default=None)
    parser.add_argument("--jobs", type=int, default=DEFAULT_JOBS)
    parser.add_argument("--list", action="store_true", help="print the versions and exit")
    parser.add_argument("--dry-run", action="store_true", help="print the commands and exit")
    args = parser.parse_args(argv)
    if not 1 <= args.jobs <= MAX_JOBS:
        parser.error(f"--jobs must be between 1 and {MAX_JOBS}")
    return args


def main(argv: list[str] | None = None) -> int:
    """Run the matrix or print it.

    Args:
        argv: The arguments; ``sys.argv[1:]`` by default.

    Returns:
        0 on success, 1 when a gate failed, 2 when the workflow cannot be parsed.
    """
    args = parse_args(argv)
    try:
        versions = matrix_versions(args.workflow)
    except (OSError, MatrixError) as exc:
        print(f"matrix: {exc}", file=sys.stderr)
        return 2
    if args.list:
        for version in versions:
            print(version)
        return 0
    if args.dry_run:
        _print_dry_run(versions, args.cache_root, args.python_dir)
        return 0
    print(f"matrix: {len(versions)} versions from {args.workflow}")
    return run_matrix(versions, args.cache_root, args.jobs, args.python_dir)


if __name__ == "__main__":
    raise SystemExit(main())

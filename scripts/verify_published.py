"""Install a released version from PyPI and use it the way a user would.

``verify-published.yml`` runs this after an upload, on every runner OS and on the oldest and
newest supported Python, and from its weekly schedule with each supported installer. It creates a
fresh environment outside the checkout, installs both exact versions (retrying while the index
catches up), then runs one conversion and one patro lookup whose results are fixed data, so a
wrong file or a wrong version fails here and not for a user.

    python scripts/verify_published.py 0.1.0b1
    python scripts/verify_published.py latest --resolve
    python scripts/verify_published.py latest --manager uv
    python scripts/verify_published.py latest --metadata
    python scripts/verify_published.py 0.1.0b1 --index-url https://test.pypi.org/simple/

``latest`` is the version a plain ``pip install nepdate-core`` gets: ``info.version`` from PyPI's
JSON API, which is the newest release, including a pre-release while only pre-releases exist. The
resolved version is printed before anything is installed. ``--resolve`` prints it alone and exits,
so a workflow can pass it to the later jobs. ``--metadata`` reads the same JSON API for both
distributions, confirms the version is listed with files that are not yanked, and sends a HEAD
request to every file, so it downloads nothing and adds nothing to PyPI's download count.
``--manager`` picks pip (the default), uv or poetry and installs with exactly that tool.
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

CORE_DIST = "nepdate-core"
PATRO_DIST = "nepdate-patro"
PYPI = "https://pypi.org/simple/"
JSON_API = "https://pypi.org/pypi/{dist}/json"
USER_AGENT = "nepdate-verify-published"
HTTP_OK = 200
HTTP_TIMEOUT_SECONDS = 30
RETRY_SECONDS = 30
# The PEP 440 spellings this repository publishes: X.Y.Z, optionally a, b or rc, post or dev.
VERSION_PATTERN = re.compile(
    r"^[0-9]+(?:\.[0-9]+)+(?:(?:a|b|rc)[0-9]+)?(?:\.post[0-9]+)?(?:\.dev[0-9]+)?$"
)
# The same date as the README quick start. Fixed data: a conversion or table change that moves
# any of these lines fails the check on purpose.
CHECK = """\
import importlib.metadata as metadata
from nepdate import Lang, NepaliDate
from nepdate_patro import info

d = NepaliDate(2080, 5, 15)
assert str(d) == "2080/05/15", str(d)
assert d.to_date().isoformat() == "2023-09-01", d.to_date()
assert d.long(weekday=True, lang=Lang.NE) == "शुक्रवार, भदौ १५, २०८०"
assert NepaliDate.parse("2080/05/15") == d
day = info(d)
assert day.tithi is not None and day.tithi.label(Lang.EN) == "Dwitiya", day.tithi
print(metadata.version("nepdate-core"), metadata.version("nepdate-patro"))
"""

Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]
Getter = Callable[[str], str]
Header = Callable[[str], int]


def _run(
    command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a command and capture its output as UTF-8 text.

    Args:
        command: The command and its arguments.
        cwd: The working directory; the caller's when None.
        env: Extra environment variables, or None.

    Returns:
        The completed process.
    """
    merged = {**os.environ, "PYTHONUTF8": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1"}
    if env:
        merged.update(env)
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        cwd=cwd,
        env=merged,
    )


def _venv_python(venv: Path) -> Path:
    """Return the interpreter inside a venv on this OS.

    Args:
        venv: The venv directory.

    Returns:
        The path of its Python executable.
    """
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def package_json(dist: str) -> str:
    """Return the PyPI metadata API URL of a distribution.

    Args:
        dist: The distribution name.

    Returns:
        The JSON endpoint a plain install reads the version from.
    """
    return JSON_API.format(dist=dist)


def _json_object(payload: str) -> dict[str, Any]:
    """Parse a JSON object from a registry response.

    Args:
        payload: The response body.

    Returns:
        The decoded object.

    Raises:
        RuntimeError: The body is not a JSON object.
    """
    data: Any = json.loads(payload)
    if not isinstance(data, dict):
        raise RuntimeError("PyPI answered with something that is not a JSON object")
    return data


def parse_latest(payload: str) -> str:
    """Return the version from PyPI's ``info.version`` field.

    Args:
        payload: The body of a PyPI JSON API response.

    Returns:
        The version exactly as PyPI spells it, for example ``0.1.0b1``.

    Raises:
        RuntimeError: The response has no usable version.
    """
    info = _json_object(payload).get("info")
    if not isinstance(info, dict):
        raise RuntimeError("PyPI JSON has no info")
    version = info.get("version")
    if not isinstance(version, str) or not version:
        raise RuntimeError("PyPI JSON has no info.version")
    return version


def latest_version(get: Getter | None = None) -> str:
    """Return the version a plain install of the core gets.

    Args:
        get: The HTTP GET helper, replaced in tests.

    Returns:
        The version from PyPI's JSON API.
    """
    return parse_latest((get or _get_text)(package_json(CORE_DIST)))


def release_files(payload: str, version: str, dist: str) -> list[dict[str, Any]]:
    """Return the files of one version that are still served.

    Args:
        payload: The body of a PyPI JSON API response.
        version: The version to look up, for example ``0.1.0b1``.
        dist: The distribution name, used in error messages.

    Returns:
        The entries of the version that are not yanked.

    Raises:
        RuntimeError: The version is missing, has no files, or every file is yanked.
    """
    releases = _json_object(payload).get("releases")
    files: Any = releases.get(version) if isinstance(releases, dict) else None
    if not isinstance(files, list) or not files:
        raise RuntimeError(f"PyPI does not list {dist} {version}")
    entries = [entry for entry in files if isinstance(entry, dict)]
    live = [entry for entry in entries if not entry.get("yanked")]
    if not live:
        raise RuntimeError(f"PyPI lists every file of {dist} {version} as yanked")
    return live


def check_metadata(
    version: str, get: Getter | None = None, head: Header | None = None
) -> list[str]:
    """Check that PyPI still lists both distributions and answers for every file.

    HEAD requests fetch headers only, so no package file is downloaded.

    Args:
        version: The version to check.
        get: The HTTP GET helper, replaced in tests.
        head: The HTTP HEAD helper, replaced in tests.

    Returns:
        One line per distribution.

    Raises:
        RuntimeError: A version is missing, yanked, or a file does not answer 200.
    """
    fetch = get or _get_text
    headers = head or _head
    lines: list[str] = []
    for dist in (CORE_DIST, PATRO_DIST):
        files = release_files(fetch(package_json(dist)), version, dist)
        for entry in files:
            url = entry.get("url")
            if not isinstance(url, str) or not url:
                raise RuntimeError(f"PyPI lists {dist} {version} without a file URL")
            code = headers(url)
            if code != HTTP_OK:
                raise RuntimeError(f"{url} answered {code}")
        count = len(files)
        plural = "" if count == 1 else "s"
        lines.append(f"verify: {dist} {version} is listed and {count} file{plural} answered 200")
    return lines


def _get_text(url: str) -> str:
    """Read a URL as text.

    Args:
        url: The URL to read.

    Returns:
        The response body.

    Raises:
        RuntimeError: The URL cannot be read.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            body: bytes = response.read()
            return body.decode("utf-8")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"cannot read {url}: {exc}") from exc


def _head(url: str) -> int:
    """Return the status code of a HEAD request.

    Args:
        url: The URL to ask about.

    Returns:
        The status code, including 404 and other error responses.

    Raises:
        RuntimeError: The host cannot be reached.
    """
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            return int(response.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)
    except urllib.error.URLError as exc:
        raise RuntimeError(f"cannot reach {url}: {exc}") from exc


def install_command(python: Path, version: str, index_url: str, extra_index_url: str) -> list[str]:
    """Return the pip command that installs both exact versions and nothing cached.

    Args:
        python: The venv interpreter.
        version: The PyPI version, for example ``0.1.0b1``.
        index_url: The index to install from.
        extra_index_url: A second index for dependencies, or an empty string.

    Returns:
        The command line.
    """
    command = [str(python), "-m", "pip", "install", "--no-cache-dir", "--index-url", index_url]
    if extra_index_url:
        command += ["--extra-index-url", extra_index_url]
    return [*command, f"{CORE_DIST}=={version}", f"{PATRO_DIST}=={version}"]


def uv_install_command(
    python: Path, version: str, index_url: str, extra_index_url: str
) -> list[str]:
    """Return the uv command that installs both exact versions.

    Args:
        python: The venv interpreter.
        version: The PyPI version, for example ``0.1.0b1``.
        index_url: The index to install from.
        extra_index_url: A second index for dependencies, or an empty string.

    Returns:
        The command line.
    """
    command = ["uv", "pip", "install", "--python", str(python), "--index-url", index_url]
    if extra_index_url:
        command += ["--extra-index-url", extra_index_url]
    return [*command, f"{CORE_DIST}=={version}", f"{PATRO_DIST}=={version}"]


def poetry_project(version: str, index_url: str, extra_index_url: str) -> str:
    """Return the pyproject.toml of the throwaway Poetry consumer.

    Poetry 2 selects a source by priority, so a non-default index becomes primary and a second
    index becomes supplemental.

    Args:
        version: The PyPI version, for example ``0.1.0b1``.
        index_url: The index to install from.
        extra_index_url: A second index for dependencies, or an empty string.

    Returns:
        The file contents.
    """
    lines = [
        "[tool.poetry]",
        'name = "verify-published"',
        'version = "0.0.0"',
        'description = ""',
        'authors = ["NepDate contributors"]',
        "package-mode = false",
        "",
        "[tool.poetry.dependencies]",
        'python = ">=3.11"',
        f'{CORE_DIST} = "=={version}"',
        f'{PATRO_DIST} = "=={version}"',
    ]
    if index_url != PYPI:
        lines += [
            "",
            "[[tool.poetry.source]]",
            'name = "verify-index"',
            f'url = "{index_url}"',
            'priority = "primary"',
        ]
    if extra_index_url:
        lines += [
            "",
            "[[tool.poetry.source]]",
            'name = "verify-extra-index"',
            f'url = "{extra_index_url}"',
            'priority = "supplemental"',
        ]
    return "\n".join(lines) + "\n"


def install_with_retries(
    command: list[str],
    wait_seconds: int,
    run: Runner = _run,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> None:
    """Run the install until it succeeds or the wait runs out.

    A new upload can take minutes to appear in the simple index, so a failed install is retried.

    Args:
        command: The pip command.
        wait_seconds: How long to keep retrying.
        run: The command runner, replaced in tests.
        sleep: The pause between attempts, replaced in tests.
        clock: A monotonic clock, replaced in tests.

    Raises:
        RuntimeError: The install still fails when the wait runs out.
    """
    deadline = clock() + wait_seconds
    while True:
        result = run(command)
        if result.returncode == 0:
            return
        left = deadline - clock()
        if left <= 0:
            tail = "\n".join((result.stdout + result.stderr).strip().splitlines()[-10:])
            raise RuntimeError(f"install failed after {wait_seconds} s:\n{tail}")
        pause = min(RETRY_SECONDS, left)
        print(f"verify: install failed, retrying in {pause:.0f} s", flush=True)
        sleep(pause)


def check_output(output: str, version: str) -> None:
    """Check that the installed distributions report the expected version.

    Args:
        output: The check program's standard output.
        version: The expected PyPI version.

    Raises:
        RuntimeError: The versions differ.
    """
    if output.split() != [version, version]:
        raise RuntimeError(f"installed versions are {output.split()}, expected {version} twice")


def _create_venv(work: Path) -> Path:
    """Create a plain virtualenv with the running interpreter.

    Args:
        work: The throwaway directory that holds it.

    Returns:
        The venv interpreter.

    Raises:
        RuntimeError: The venv cannot be created.
    """
    venv = work / "venv"
    created = _run([sys.executable, "-m", "venv", str(venv)])
    if created.returncode != 0:
        raise RuntimeError(f"venv failed: {created.stderr.strip()}")
    return _venv_python(venv)


def _create_uv_venv(work: Path) -> Path:
    """Create a virtualenv with uv and the running interpreter.

    Args:
        work: The throwaway directory that holds it.

    Returns:
        The venv interpreter.

    Raises:
        RuntimeError: The venv cannot be created.
    """
    venv = work / "venv"
    created = _run(
        ["uv", "venv", str(venv), "--python", sys.executable],
        env={"UV_CACHE_DIR": str(work / "uv-cache")},
    )
    if created.returncode != 0:
        raise RuntimeError(f"uv venv failed: {created.stderr.strip()}")
    return _venv_python(venv)


def _create_poetry_project(
    work: Path, version: str, index_url: str, extra_index_url: str
) -> tuple[Path, dict[str, str]]:
    """Write the Poetry consumer and return it with its isolated cache settings.

    Args:
        work: The throwaway directory that holds it.
        version: The PyPI version, for example ``0.1.0b1``.
        index_url: The index to install from.
        extra_index_url: A second index for dependencies, or an empty string.

    Returns:
        The project directory and the environment that keeps Poetry's caches inside it.
    """
    project = work / "poetry-project"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        poetry_project(version, index_url, extra_index_url), encoding="utf-8"
    )
    env = {
        "POETRY_CACHE_DIR": str(work / "poetry-cache"),
        "POETRY_VIRTUALENVS_PATH": str(work / "poetry-venvs"),
        "POETRY_VIRTUALENVS_IN_PROJECT": "false",
        "POETRY_NO_INTERACTION": "1",
        "POETRY_ANSI": "never",
    }
    return project, env


def _run_check(python: Path, cwd: Path, version: str) -> None:
    """Run the check program in an environment and compare its output.

    Args:
        python: The environment's interpreter.
        cwd: The throwaway directory to run from, so nothing in the checkout can shadow the
            installed packages.
        version: The expected PyPI version.

    Raises:
        RuntimeError: The program exits non-zero or reports another version.
    """
    result = _run([str(python), "-c", CHECK], cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"check failed:\n{result.stdout}{result.stderr}")
    check_output(result.stdout, version)


def verify(
    version: str,
    index_url: str,
    extra_index_url: str,
    wait_seconds: int,
    manager: str = "pip",
) -> None:
    """Install both distributions into a fresh environment with one manager and run the check.

    Args:
        version: The PyPI version, for example ``0.1.0b1``.
        index_url: The index to install from.
        extra_index_url: A second index for dependencies, or an empty string.
        wait_seconds: How long to retry the install.
        manager: ``pip``, ``uv`` or ``poetry``.

    Raises:
        RuntimeError: The environment, the install or the check fails.
    """
    with tempfile.TemporaryDirectory(prefix="nepdate-verify-") as tmp:
        work = Path(tmp)
        if manager == "uv":
            python = _create_uv_venv(work)
            command = uv_install_command(python, version, index_url, extra_index_url)
            uv_env = {"UV_CACHE_DIR": str(work / "uv-cache")}
            install_with_retries(command, wait_seconds, run=functools.partial(_run, env=uv_env))
            _run_check(python, work, version)
        elif manager == "poetry":
            project, poetry_env = _create_poetry_project(work, version, index_url, extra_index_url)
            install_with_retries(
                ["poetry", "install", "--no-interaction", "--no-ansi"],
                wait_seconds,
                run=functools.partial(_run, cwd=project, env=poetry_env),
            )
            # Poetry's Windows runner splits a multi-line -c argument, so the program is a file.
            check_file = project / "check.py"
            check_file.write_text(CHECK, encoding="utf-8")
            result = _run(["poetry", "run", "python", str(check_file)], cwd=project, env=poetry_env)
            if result.returncode != 0:
                raise RuntimeError(f"check failed:\n{result.stdout}{result.stderr}")
            check_output(result.stdout, version)
        else:
            python = _create_venv(work)
            command = install_command(python, version, index_url, extra_index_url)
            install_with_retries(command, wait_seconds)
            _run_check(python, work, version)
    tool = "" if manager == "pip" else f" with {manager}"
    print(f"verify: {CORE_DIST} and {PATRO_DIST} {version} from {index_url}{tool}: ok")


def main(argv: list[str] | None = None) -> int:
    """Parse the arguments and resolve, check metadata for, or install one released version.

    Args:
        argv: The command line arguments; ``sys.argv[1:]`` when None.

    Returns:
        0 on success, 1 when the check fails, 2 on a bad version.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "version", nargs="?", default="latest", help="the PyPI version, for example 0.1.0b1"
    )
    parser.add_argument("--index-url", default=PYPI)
    parser.add_argument("--extra-index-url", default="")
    parser.add_argument("--wait-seconds", type=int, default=900)
    parser.add_argument("--manager", choices=("pip", "uv", "poetry"), default="pip")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--resolve", action="store_true", help="print the version and exit")
    mode.add_argument("--metadata", action="store_true", help="check PyPI's metadata only")
    args = parser.parse_args(argv)
    try:
        version = args.version
        if version == "latest":
            version = latest_version()
            if not args.resolve:
                print(f"verify: PyPI latest is {version}")
        if args.resolve:
            print(version)
            return 0
        if not VERSION_PATTERN.fullmatch(version):
            print(f"verify: '{version}' is not a PEP 440 version like 0.1.0b1", file=sys.stderr)
            return 2
        if args.metadata:
            for line in check_metadata(version):
                print(line)
            return 0
        verify(version, args.index_url, args.extra_index_url, args.wait_seconds, args.manager)
    except RuntimeError as exc:
        print(f"verify: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

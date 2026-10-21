"""Measure the best import time of the core, the patro and the stdlib floor.

The gate has a coarse ceiling and checks what each import loads. This script records the
ADR-0002 §7 numbers for ``docs/benchmarks.md``: best of five ``-X importtime`` runs, with the
machine load sampled before each run. A sample taken at or above the 15 % load limit is retried;
a batch without five quiet samples is written with ``"quiet": false`` and exits 1, so it cannot
become a verdict.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parent.parent
FIELD_COUNT = 3
LOAD_LIMIT = 15.0
TARGET_SAMPLES = 5
MAX_ATTEMPTS = 30
RETRY_PAUSE_S = 0.5


def _parse(output: str, modules: tuple[str, ...]) -> int | None:
    """Read the modules' cumulative microseconds from ``-X importtime`` output.

    Args:
        output: The stderr of the import-time run.
        modules: The modules whose entries are summed.

    Returns:
        The cumulative microseconds, or None when a module is absent.
    """
    total = 0
    found = 0
    for line in output.splitlines():
        if not line.startswith("import time:"):
            continue
        parts = line.split("|")
        if len(parts) != FIELD_COUNT:
            continue
        if parts[2].strip() in modules:
            total += int(parts[1].strip())
            found += 1
    return total if found == len(modules) else None


def measure(statement: str, modules: tuple[str, ...]) -> dict[str, float | int]:
    """Measure one import five times and keep the best.

    Args:
        statement: The ``-c`` script to run.
        modules: The modules whose cumulative times are summed.

    Returns:
        The best microseconds, the five quiet samples, their loads, the load range and the
        number of attempts.
    """
    samples: list[int] = []
    loads: list[float] = []
    attempts = 0
    while len(samples) < TARGET_SAMPLES and attempts < MAX_ATTEMPTS:
        attempts += 1
        load = psutil.cpu_percent(interval=0.1)
        if load >= LOAD_LIMIT:
            time.sleep(RETRY_PAUSE_S)
            continue
        result = subprocess.run(
            [sys.executable, "-X", "importtime", "-c", statement],
            capture_output=True,
            text=True,
            check=False,
        )
        value = _parse(result.stderr, modules)
        if value is not None:
            samples.append(value)
            loads.append(load)
    return {
        "us": min(samples) if samples else 0,
        "samples": samples,
        "loads": loads,
        "load_min": min(loads) if loads else 0.0,
        "load_mean": round(sum(loads) / len(loads), 1) if loads else 0.0,
        "load_max": max(loads) if loads else 0.0,
        "attempts": attempts,
    }


def main() -> int:
    """Measure the three imports and write ``import_time.json`` for today.

    Returns:
        0 when every module has five quiet samples, 1 otherwise.
    """
    day = date.today().isoformat()
    output = ROOT / "benchmarks" / "results" / day
    output.mkdir(parents=True, exist_ok=True)
    core = measure("import nepdate", ("nepdate",))
    patro = measure("import nepdate; import nepdate_patro", ("nepdate_patro",))
    floor = measure("import datetime, enum", ("datetime", "enum"))
    complete = all(len(result["samples"]) == TARGET_SAMPLES for result in (core, patro, floor))
    load_max = max(float(result["load_max"]) for result in (core, patro, floor))
    quiet = complete and load_max < LOAD_LIMIT
    data = {
        "date": day,
        "python": sys.version,
        "limit": LOAD_LIMIT,
        "quiet": quiet,
        "nepdate": core,
        "nepdate_patro": patro,
        "datetime_enum": floor,
    }
    (output / "import_time.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    if not complete:
        print(
            "import-time: a module did not appear or five quiet samples did not arrive",
            file=sys.stderr,
        )
        return 1
    if not quiet:
        print(f"import-time: load reached {load_max} %; no verdict", file=sys.stderr)
        return 1
    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

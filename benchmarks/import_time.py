"""Measure the best import time of the core and the patro, with the load beside it.

The gate has a coarse ceiling and checks what each import loads. This script records the
ADR-0002 §7 numbers for ``docs/benchmarks.md``: best of five ``-X importtime`` runs, with the
machine load sampled around each run.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parent.parent
FIELD_COUNT = 3


def _parse(output: str, module: str) -> int | None:
    """Read a module's cumulative microseconds from ``-X importtime`` output.

    Args:
        output: The stderr of the import-time run.
        module: The module whose entry is wanted.

    Returns:
        The cumulative microseconds, or None when the module is absent.
    """
    for line in output.splitlines():
        if not line.startswith("import time:"):
            continue
        parts = line.split("|")
        if len(parts) != FIELD_COUNT:
            continue
        if parts[2].strip() == module:
            return int(parts[1].strip())
    return None


def measure(statement: str, module: str) -> dict[str, float | int]:
    """Measure one import five times and keep the best.

    Args:
        statement: The ``-c`` script to run.
        module: The module whose cumulative time is read.

    Returns:
        The best microseconds, all samples, and the load range during the runs.
    """
    samples: list[int] = []
    loads: list[float] = []
    for _ in range(5):
        loads.append(psutil.cpu_percent(interval=0.1))
        result = subprocess.run(
            [sys.executable, "-X", "importtime", "-c", statement],
            capture_output=True,
            text=True,
            check=False,
        )
        value = _parse(result.stderr, module)
        if value is not None:
            samples.append(value)
    return {
        "us": min(samples),
        "samples": samples,
        "load_min": min(loads),
        "load_mean": round(sum(loads) / len(loads), 1),
        "load_max": max(loads),
    }


def main() -> int:
    """Measure both imports and write ``import_time.json`` for today.

    Returns:
        0 when both modules appeared, 1 otherwise.
    """
    day = date.today().isoformat()
    output = ROOT / "benchmarks" / "results" / day
    output.mkdir(parents=True, exist_ok=True)
    core = measure("import nepdate", "nepdate")
    patro = measure("import nepdate; import nepdate_patro", "nepdate_patro")
    data = {"date": day, "python": sys.version, "nepdate": core, "nepdate_patro": patro}
    (output / "import_time.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    if not core["samples"] or not patro["samples"]:
        print("import-time: a module did not appear", file=sys.stderr)
        return 1
    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Run every benchmark in its own process and record the machine load next to it.

Run from the repository root with ``uv run --group bench python benchmarks/run.py``. Each
benchmark is a separate pyperf process, pinned by pyperf's ``--affinity 2``, and the CPU load is
sampled while that process runs. The numbers go to ``benchmarks/results/<date>/``; this script
does not tune the machine and does not edit ``docs/benchmarks.md``.
"""

from __future__ import annotations

import json
import statistics
import subprocess
import sys
import time
from datetime import date as date_type
from datetime import datetime
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from benchmarks import bench  # noqa: E402 - ROOT must be on sys.path first

AFFINITY = 2
TIMEOUT_S = 180


def _load_sample() -> dict[str, float | int]:
    """Take one machine load sample.

    Returns:
        CPU percent over all cores, memory percent, and the number of processes.
    """
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory_percent": psutil.virtual_memory().percent,
        "processes": len(psutil.pids()),
    }


def _summarise(samples: list[dict[str, float | int]]) -> dict[str, float | int]:
    """Summarise the load samples of one benchmark process.

    Args:
        samples: The samples taken while the process ran.

    Returns:
        Min, mean, median and max CPU percent, the mean memory percent, the process count and
        the number of samples.
    """
    cpu = [float(sample["cpu_percent"]) for sample in samples] or [0.0]
    return {
        "cpu_min": min(cpu),
        "cpu_mean": round(statistics.mean(cpu), 1),
        "cpu_median": round(statistics.median(cpu), 1),
        "cpu_max": max(cpu),
        "memory_mean": round(
            statistics.mean(float(sample["memory_percent"]) for sample in samples)
            if samples
            else 0.0,
            1,
        ),
        "processes": max((int(sample["processes"]) for sample in samples), default=0),
        "samples": len(samples),
    }


def _values(result: dict[str, object]) -> list[float]:
    """Return the measured values of the first benchmark in a pyperf result.

    Args:
        result: The parsed pyperf JSON document.

    Returns:
        The per-operation times in seconds, from every measured run.
    """
    benchmark = result["benchmarks"][0]  # type: ignore[index]
    return [
        float(value)
        for run in benchmark["runs"]  # type: ignore[index]
        if "values" in run
        for value in run["values"]
    ]


def run_one(key: str, output: Path) -> dict[str, object]:
    """Run one benchmark and sample the load while it runs.

    Args:
        key: ``b1`` or ``b1:<package>``.
        output: The pyperf JSON path.

    Returns:
        The summary row, including the load and the per-operation time.
    """
    output.unlink(missing_ok=True)
    command = [
        sys.executable,
        str(ROOT / "benchmarks" / "bench.py"),
        "--only",
        key,
        "-o",
        str(output),
        "--rigorous",
        "--quiet",
    ]
    started = time.perf_counter()
    samples: list[dict[str, float | int]] = []
    log_path = output.with_suffix(".log")
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        timed_out = False
        while process.poll() is None:
            if time.perf_counter() - started > TIMEOUT_S:
                timed_out = True
                for child in psutil.Process(process.pid).children(recursive=True):
                    child.kill()
                process.kill()
                break
            samples.append(_load_sample())
        process.wait()
    stdout = log_path.read_text(encoding="utf-8")
    elapsed = time.perf_counter() - started
    if timed_out:
        return {
            "key": key,
            "error": f"timed out after {TIMEOUT_S}s",
            "load": _summarise(samples),
        }
    if process.returncode != 0:
        return {"key": key, "error": stdout.strip()[-2000:], "load": _summarise(samples)}
    result = json.loads(output.read_text(encoding="utf-8"))
    values = _values(result)
    return {
        "key": key,
        "name": result["metadata"]["name"],  # type: ignore[index]
        "runs": len(values),
        "inner_loops": result["metadata"]["inner_loops"],  # type: ignore[index]
        "ns_op": round(statistics.mean(values) * 1e9, 2),
        "stdev_ns": round(statistics.stdev(values) * 1e9, 2),
        "elapsed_s": round(elapsed, 1),
        "last_line": stdout.strip().splitlines()[-1] if stdout.strip() else "",
        "load": _summarise(samples),
    }


def main(argv: list[str] | None = None) -> int:
    """Run all benchmarks or the requested subset.

    Args:
        argv: Command line arguments. ``--date YYYY-MM-DD`` sets the result directory;
            ``--only KEY`` may be repeated to run a subset.

    Returns:
        0 when every benchmark ran, 1 when one failed.
    """
    if argv is None:
        argv = sys.argv[1:]
    day = date_type.today().isoformat()
    selected: list[str] = []
    index = 0
    while index < len(argv):
        if argv[index] == "--date":
            day = argv[index + 1]
            index += 2
        elif argv[index] == "--only":
            selected.append(argv[index + 1])
            index += 2
        else:
            print(f"run: unknown argument {argv[index]}", file=sys.stderr)
            return 2
    out_dir = ROOT / "benchmarks" / "results" / day
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "probe.json").write_text(
        json.dumps(bench.probe(), indent=2) + "\n", encoding="utf-8"
    )
    keys = selected or list(bench._KEYS)
    rows = []
    failed = False
    for number, key in enumerate(keys, start=1):
        print(f"run: {number}/{len(keys)} {key}", flush=True)
        row = run_one(key, out_dir / (key.replace(":", "-") + ".json"))
        rows.append(row)
        if "error" in row:
            failed = True
            print(f"run: {key} failed: {row['error']}", file=sys.stderr)
        else:
            print(f"run: {key} {row['ns_op']} ns/op, CPU {row['load']['cpu_mean']}%", flush=True)
    summary = {
        "date": day,
        "generated": datetime.now().astimezone().isoformat(timespec="seconds"),
        "python": sys.version,
        "platform": sys.platform,
        "affinity": AFFINITY,
        "command": "uv run --group bench python benchmarks/run.py --date " + day,
        "probe": bench.probe(),
        "benchmarks": rows,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

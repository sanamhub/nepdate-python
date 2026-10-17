# ADR-0004: Testing and quality gates

- Status: Accepted
- Date: 2026-09-25 (amended 2026-10-07 for hub ADR-0004: core and patro are checked apart)
- Deciders: Sanam Pakuwal

## Decision

`uv run python scripts/ci.py` runs, in order, stopping at the first failure. It first runs
`uv sync --all-packages` so both workspace members are installed.

1. `ruff format --check` and `ruff check` (rules `E, F, W, I, UP, B, SIM, RUF, PL, N, D` with the
   Google docstring convention) over the whole repository.
2. `mypy --strict src packages/nepdate-patro/src scripts`.
3. `pytest tests packages/nepdate-patro/tests scripts/tests` and the README doctests, with the
   docstring examples in `_date.py` and `nepdate_patro/__init__.py`, and coverage (`pytest-cov`):
   ≥ 90 % for `nepdate` and ≥ 90 % for `nepdate_patro`, each measured on its own (org target 80 %).
4. `python scripts/codegen.py --check`.
5. `python -X importtime -c "import nepdate"`: the cumulative time of the `nepdate` entry is under 5 ms
   (ADR-0002 §7), parsed by the script. The same output must contain no `nepdate_patro` entry.
   Then `python -X importtime -c "import nepdate; import nepdate_patro"`: the cumulative time of the
   `nepdate_patro` entry is under 10 ms. Each check takes the best of 3 runs.
6. **Core on its own:** `uv build --all-packages` (wheel and sdist for both into `dist/`), then:
   - the core wheel's `METADATA` has no `Requires-Dist` line naming `nepdate-patro`;
   - no file inside the core wheel or core sdist contains the bytes `World Day Against Human Trafficking` (the script opens
     them with `zipfile` and `tarfile`, so it works on Windows without `unzip` or `grep`);
   - a fresh venv with only the core wheel plus `pytest` and `hypothesis` installed runs
     `python -m pytest tests` (the core suite) against the installed wheel, and
     `import nepdate_patro` fails there with `ModuleNotFoundError`.
7. **Patro on its own:** both wheels have the same version; the patro wheel's `Requires-Dist` for
   the core has the same-minor range of ADR-0001 §1; a fresh venv with the core wheel, the patro
   wheel, `pytest` and `hypothesis` runs `python -m pytest packages/nepdate-patro/tests`.
8. **Docs:** `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md` and `docs/*.md` have no
   em dash, no task ID and no relative link that does not resolve. Plans and ADRs keep their task
   IDs and are not part of this gate.

Gates 6 and 7 run pytest with `-o addopts=""` so only the named test directory runs, against the
installed wheels. The pytest config never sets `pythonpath = ["src"]`, so `src/` can't shadow a
wheel. The last line is `ci: 8/8 gates passed` (or names the gate that failed).

Tests:
- Core tests live in `tests/`, patro tests in `packages/nepdate-patro/tests/`, generator and CI
  script tests in `scripts/tests/`. A core test never imports `nepdate_patro`.
- **Vectors:** every file in `shared/spec/vectors/`, located from `tests/conftest.py` (path relative to
  the repository root, not the working directory). The patro suite has its own `conftest.py` that
  finds `shared/data/patro/` the same way.
- **Exhaustive:** every serial 0..=109211 round-trips BS → date → BS.
- **Properties (hypothesis):** `from_date(to_date(d)) == d`; `parse(d.isoformat()) == d`;
  `add_days(n).days_until(d) == -n`; `parse_lenient` never raises anything but `NepDateError`.
- **Doctests** in the README and docstrings run under pytest (`--doctest-glob`).
- **Negative numbers:** tests for `add_months` with negative `n` and diffs across the epoch, because
  Python's `//` floors where C# truncates.

CI: `ubuntu-latest`, `windows-latest`, `macos-latest` × 3.11–3.14, plus 3.14t on Linux and the 3.15
pre-release (allowed to fail). Actions pinned by SHA, `permissions: contents: read`. Benchmarks are
not run per PR.

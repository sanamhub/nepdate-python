# Release runbook

The two distributions, `nepdate-core` and `nepdate-patro`, are released together from one tag
(ADR-0005). The human tags. The agent runs the checks below and stops.

## Before the tag

Run the local CI matrix on every Python in `.github/workflows/ci.yml`:

```console
uv run python scripts/ci_matrix.py
```

The runner reads the workflow file, uses a separate environment for each version under
`D:\devcache\p10` on Windows (or `/mnt/d/devcache/p10` on WSL), and starts at most two versions at
a time. A version that uv cannot provide is printed as `skip`, never as passed.

Check the data and the version:

```console
uv run python scripts/data_status.py
uv run python scripts/ci.py release-check 0.1.0
```

`data_status` reads `shared/data/patro/*.json` directly. Public holidays must have at least 183 days
left on the release date; tithi and events print a warning. Use `--today YYYY-MM-DD` to check
another date. A failure is fixed by updating the hub data and merging the `shared-sync` pull
request, not by lowering the threshold.

`release-check` checks both `pyproject.toml` versions, the patro dependency range, the dated
changelog section, the data freshness rule and the release rehearsal. It prints a tithi warning
when one applies. Pass `--today YYYY-MM-DD` after the version to use another data date.

## Rehearsal

The rehearsal builds four artifacts in a temporary directory and uploads nothing:

```console
uv run python scripts/ci.py release-rehearsal
```

It builds both sdists and both wheels, runs `twine check` from the pinned `release` group, and
checks:

- no wheel contains a `tests`, `fuzz` or `docs` path, or a `test_*.py` file;
- the core sdist has `LICENSE`, `shared/data/NOTICE` and
  `shared/data/calendar/bs-calendar.json`;
- the patro sdist has `LICENSE`, `NOTICE` and the `shared/data/patro/*.json` source that generated
  `_tables.py`;
- the two wheel versions, the installed package metadata and the changelog agree.

The release build stages the patro source data next to the package before `uv build`, so the sdist
and the rehearsal use the same inputs:

```console
uv run python scripts/ci.py build-release
uv run python scripts/ci.py sort-dist
```

`build-release` writes the four files to `dist/`; `sort-dist` moves them to `dist/core/` and
`dist/patro/`. Do not upload them by hand.

## The tag

`.github/workflows/release.yml` runs the preflight, CI, build, mutation and fuzz jobs before the
environment-gated publish. A tag push publishes to PyPI; a dispatch run publishes to TestPyPI. The
publish job checks that the tagged commit is on `origin/main` and uses trusted publishing. There is
no API token in the repository.

If the core upload succeeds and the patro upload fails, rerun the job: the core step has
`skip-existing: true`, and the patro step does not. To undo a release, yank both files and publish
the next patch version (ADR-0005).

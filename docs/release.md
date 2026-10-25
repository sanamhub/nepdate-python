# Release runbook

The two distributions, `nepdate-core` and `nepdate-patro`, are released together from one tag
(ADR-0005). Run the checks below, then the maintainer tags.

## Before the tag

Run the local CI matrix on every Python in `.github/workflows/ci.yml`:

```console
uv run python scripts/ci_matrix.py
```

The runner reads the workflow file, uses a separate environment for each version under
`--cache-root` (default `nepdate-ci-matrix` in the system temporary directory), and starts at most two versions at
a time. A version that uv cannot provide is printed as `skip`, never as passed.

Check the data and the version:

```console
uv run python scripts/data_status.py
uv run python scripts/ci.py release-check 0.1.0-beta.1
```

`data_status` reads `shared/data/patro/*.json` directly and counts from today's UTC date, as every
port does. Public holidays must have at least 183 days left on the release date; tithi and events
print a warning. Use `--today YYYY-MM-DD` to check another date. A failure is fixed by updating the hub data and merging the `shared-sync` pull
request, not by lowering the threshold.

`release-check` checks both `pyproject.toml` versions, the patro dependency range, the dated
changelog section and that `[Unreleased]` has no entries. It also checks the data freshness rule.
It builds nothing. It prints a tithi warning when one applies. Pass `--today YYYY-MM-DD` after the
version to use another data date.

## Rehearsal

Locally, the rehearsal builds four artifacts in a temporary directory and uploads nothing:

```console
uv run python scripts/ci.py release-rehearsal
```

It builds both sdists and both wheels with a plain `uv build --all-packages`, runs `twine check` from the pinned `release` group, and
checks:

- no wheel contains a `tests`, `fuzz` or `docs` path, or a `test_*.py` file;
- the core sdist has `LICENSE`, `shared/data/NOTICE` and
  `shared/data/calendar/bs-calendar.json`;
- the patro sdist has `LICENSE`, `NOTICE` and the `shared/data/patro/*.json` source that generated
  `_tables.py`;
- the two wheel versions, the installed package metadata and the changelog agree.

The patro sdist gets its JSON from hatchling's `force-include` of `../../shared/data/patro`
(ADR-0011), so a direct `uv build` and the release build give the same files, and a build without
that folder fails. The release workflow builds once and checks the files it will publish:

```console
uv run python scripts/ci.py build-release
uv run python scripts/ci.py release-rehearsal 0.1.0-beta.1 --dist dist
uv run python scripts/ci.py sort-dist
```

`build-release` writes the four files to `dist/`; `release-rehearsal --dist` checks them without
building; `sort-dist` moves them to `dist/core/` and `dist/patro/`. Do not upload them by hand.

## The tag

`.github/workflows/release.yml` runs the preflight, CI, build, mutation and fuzz jobs before the
environment-gated publish. A tag push publishes to PyPI; a dispatch run publishes to TestPyPI. The
publish job checks that the tagged commit is on `origin/main` and uses trusted publishing. There is
no API token in the repository.

If the core upload succeeds and the patro upload fails, do not tag again. The
[detailed release runbook](runbooks/release.md#if-only-the-core-was-published) explains which step
can be re-run, why `skip-existing` is set only on the core, and when the patro files are too
incomplete to retry.

## After the publish

A tag run publishes to PyPI, then the `verify` job calls `verify-published.yml`, which installs
both exact versions with pip in a fresh venv outside the checkout, on Linux, macOS and Windows with
Python 3.11 and 3.14. A dispatch dry run publishes to TestPyPI, then `verify-testpypi` does the
same against `https://test.pypi.org/simple/`, with PyPI as a second index for `tzdata` on Windows.
Each install is retried for up to 15 minutes while the index catches up. The check
(`scripts/verify_published.py`) runs the README quick start and one `nepdate_patro.info` call and
compares both installed versions. The jobs are read-only: `contents: read`, no `id-token`, and no
upload. The workflow can also be run by hand for any version already on PyPI.

The GitHub Release is created by the `github-release` job, which needs `verify`. It is the only
job with `contents: write`. When verify fails there is no release page, only the PyPI files to
yank.

If a verify job fails, the release is not done. Do not upload the same files again and do not
publish a different build under the same version. Yank both distributions for that version, fix
the cause, and publish the next patch version of both (ADR-0005). A TestPyPI failure is a failed
rehearsal: yank both TestPyPI files and use the next patch version for the next run.

# ADR-0005: Releases

- Status: Accepted
- Date: 2026-09-25 (amended 2026-10-07 for hub ADR-0004: two distributions, one release)
- Deciders: Sanam Pakuwal

## Decision

- `<core-name>` is the core distribution name (ADR-0001 §1, ADR-0007).
- The core and `nepdate-patro` always have the same version and are released together from one tag
  (hub ADR-0004 §3). A data change that touches only the patro still releases both (patch).
- The version is written in the two `pyproject.toml` files and nowhere else; `nepdate.__version__`
  reads `importlib.metadata.version("<core-name>")`. Semver. The patro dependency on the core is
  `>=X.Y,<X.(Y+1)` for the version being released.
- One `CHANGELOG.md` (Keep a Changelog) for both distributions. Tag `vX.Y.Z`.
  `scripts/ci.py release-check X.Y.Z` checks that the tag, both `pyproject.toml` versions, the patro
  dependency range and a changelog section agree.
- `release.yml` on tag `v*`, and `workflow_dispatch` with `dry-run` (default `true`):
  preflight (release-check) → CI → build sdist + wheel of both distributions once
  (`uv build --all-packages`) → `environment: production` (required reviewer) → publish with
  **PyPI trusted publishing** (`pypa/gh-action-pypi-publish`, `id-token: write`), which also uploads
  PEP 740 attestations. The build job sorts the files into `dist/core/` and `dist/patro/` by file
  name. Two publish steps in the same job (`packages-dir: dist/core/`, then `dist/patro/`), so
  `nepdate-patro==X.Y.Z` never appears on PyPI before the core it needs → GitHub Release with
  notes from the changelog section and all four files attached → a job that installs
  `<core-name>==X.Y.Z nepdate-patro==X.Y.Z` from PyPI in a clean venv and runs the README example
  and one `nepdate_patro.info` call (retries for 10 minutes).
- A dry run publishes the same way to TestPyPI (environment `testpypi`) instead of PyPI.
- Trusted publishers: each PyPI project needs its own. Before the first release, register a
  **pending publisher** for both `<core-name>` and `nepdate-patro` on PyPI (environment
  `production`) and on TestPyPI (environment `testpypi`): four registrations, all with repository
  `sanamhub/nepdate-python` and workflow `release.yml`.
- Rollback: PyPI files can't be replaced. **Yank** the release of both distributions (it stays
  installable only by exact pin) and publish `X.Y.(Z+1)` of both.

## Consequences

- No API token exists anywhere.
- The weekly `shared-sync` PR, once merged, is released as a patch version of both distributions.
- If the core upload succeeds and the patro upload fails, the core version is already public.
  The core publish step sets `skip-existing: true`, so re-running the failed job (same built files)
  skips the core and uploads only the patro. The patro step doesn't set it.

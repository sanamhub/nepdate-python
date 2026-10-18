# Runbook: release the core and `nepdate-patro` (Python)

Decided in ADR-0005 and ADR-0007. Owner: maintainer. Approver: a second person. One tag releases
both distributions with the same version. The core distribution is `nepdate-core`, chosen in
P0-06; its import name is `nepdate`.

## One-time setup (before the first release)

1. On PyPI and on TestPyPI, add a **pending publisher** for each project: `nepdate-core` and
   `nepdate-patro`. Owner `sanamhub`, repository `nepdate-python`, workflow `release.yml`,
   environment `production` on PyPI and `testpypi` on TestPyPI. Four entries in total.
2. In the GitHub repository, create the environments `production` (required reviewer) and
   `testpypi`.

## Before tagging

1. `main` is green. `uv run python scripts/ci.py` passes locally.
2. Both `pyproject.toml` files (root and `packages/nepdate-patro/`) have version `X.Y.Z`; the patro
   dependency is `nepdate-core>=X.Y,<X.(Y+1)`; `CHANGELOG.md` has `## [X.Y.Z] - YYYY-MM-DD`.
3. `uv run python scripts/ci.py release-check X.Y.Z` passes. It checks both `pyproject.toml`
   versions, the patro range and the dated `## [X.Y.Z] - YYYY-MM-DD` changelog heading.
4. Optional: run `release.yml` by hand with the `version` input and `dry-run: true` to publish to
   TestPyPI first. A dispatch never publishes to PyPI; only a `v*` tag does. TestPyPI also refuses
   a version twice, so a second dry run of the same version needs `skip-existing` on that step or a
   new pre-release version.

## Releasing

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

`release.yml` runs preflight, CI and the build, waits for the `production` approval, publishes the
core and then `nepdate-patro` to PyPI by trusted publishing (with attestations), creates the
GitHub Release from the changelog section, then installs `nepdate-core==X.Y.Z` and
`nepdate-patro==X.Y.Z` from PyPI and runs the README example.

## After releasing

1. Both PyPI pages show the version and "Verified details" (attestation).
2. Add an empty `## [Unreleased]` to the changelog.

## If only the core was published

The patro upload failed after the core upload. Fix the cause (for example a missing pending
publisher for `nepdate-patro`), then use "Re-run failed jobs" on the same workflow run. The core
step has `skip-existing: true`, so it skips the files already on PyPI and only the patro is uploaded
(ADR-0005). Don't tag again.

## Rolling back

PyPI files can't be replaced or reused. Yank `X.Y.Z` of both projects on PyPI (Manage → Options →
Yank) with a reason, release `X.Y.(Z+1)` of both with the fix, and note both in the changelog.

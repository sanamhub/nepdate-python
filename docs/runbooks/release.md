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
4. The release commit is on `origin/main`. The publish job fetches `origin/main` and runs
   `git merge-base --is-ancestor` on the tagged commit; a tag on a side branch fails before any
   upload.
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

The core step needs `skip-existing` because it is not the last upload: a patro failure leaves a
public core, and the same run must be restartable without a duplicate-file error. The patro step
does not set it because it is the last upload. If the patro step fails after some of its files are
already on PyPI, a re-run fails on those files instead of skipping them. That is deliberate: check
the project page, and if the patro files are incomplete, publish `X.Y.(Z+1)` of both rather than
assuming the release is complete. The TestPyPI dry run sets `skip-existing` on both steps because a
second dry run of the same version is a normal retry.

## Rolling back

PyPI files can't be replaced or reused. Yank `X.Y.Z` of both projects on PyPI (Manage → Options →
Yank) with a reason, release `X.Y.(Z+1)` of both with the fix, and note both in the changelog.

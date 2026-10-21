# Runbook: release the core and `nepdate-patro` (Python)

Decided in ADR-0005 and ADR-0007. Owner: maintainer. Approver: a second person. One tag releases
both distributions with the same version. The core distribution is `nepdate-core`, chosen in
P0-06; its import name is `nepdate`.

## One-time setup (before the first release)

1. On PyPI and on TestPyPI, add a **pending publisher** for each project, owner `sanamhub`,
   repository `nepdate-python`, workflow `release.yml`. Four entries in total:

   | Project | PyPI environment | TestPyPI environment |
   |---|---|---|
   | `nepdate-core` | `production` | `testpypi` |
   | `nepdate-patro` | blank | blank |

   PyPI refuses a second pending publisher with the same repository, workflow and environment for
   another project ("A pending trusted publisher matching this configuration has already been
   registered for a different project name"), so the patro entry leaves the environment blank.
   The workflow still publishes it from the `production` job; the step under "After the first
   release" narrows it once the project exists.
2. In the GitHub repository, create the environments `production` (required reviewer, `v*` tags
   only) and `testpypi` (`main` and `v*` tags).

## Before tagging

1. `main` is green. `uv run python scripts/ci.py` passes locally.
2. Both `pyproject.toml` files (root and `packages/nepdate-patro/`) have the PyPI spelling of the
   version; the patro dependency is `nepdate-core>=X.Y,<X.(Y+1)`; `CHANGELOG.md` has
   `## [X.Y.Z] - YYYY-MM-DD`. For a pre-release see below.
3. `uv run python scripts/ci.py release-check X.Y.Z` passes. It checks both `pyproject.toml`
   versions, the patro range and the dated changelog heading.
4. The release commit is on `origin/main`. The publish job fetches `origin/main` and runs
   `git merge-base --is-ancestor` on the tagged commit; a tag on a side branch fails before any
   upload.
4. Optional: run `release.yml` by hand with the `version` input and `dry-run: true` to publish to
   TestPyPI first. A dispatch never publishes to PyPI; only a `v*` tag does. TestPyPI also refuses
   a version twice, so a second dry run of the same version needs `skip-existing` on that step or a
   new pre-release version.

## Pre-releases

The tag and the changelog use the same spelling as every other NepDate port, `0.1.0-beta.1`. PyPI
needs PEP 440, so the pyprojects and the files say `0.1.0b1` (`scripts/versions.py` maps one to the
other; only `alpha`, `beta` and `rc` are accepted). For `v0.1.0-beta.1`:

- both pyprojects: `version = "0.1.0b1"`;
- patro dependency: `nepdate-core>=0.1.0b1,<0.2`. The lower bound names the beta because pip
  takes a pre-release only when a specifier mentions one; `>=0.1` would refuse `0.1.0b1`;
- changelog: `## [0.1.0-beta.1] - YYYY-MM-DD`. A stable section does not satisfy a beta tag, nor
  the other way round;
- `release-check 0.1.0-beta.1` and `pypi-version 0.1.0-beta.1` (prints `0.1.0b1`).

The GitHub Release is marked as a pre-release. Users install it with
`pip install --pre nepdate-core nepdate-patro` or by pinning `==0.1.0b1`.

## Releasing

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

`release.yml` runs preflight, CI and the build, waits for the `production` approval, publishes the
core and then `nepdate-patro` to PyPI by trusted publishing (with attestations), then calls
`verify-published.yml`, which installs both exact versions from PyPI with pip on Linux, macOS and
Windows with Python 3.11 and 3.14 and runs the README example and one patro lookup. Only then does
it create the GitHub Release, from the changelog section plus install and verification notes.

## After releasing

1. Both PyPI pages show the version and "Verified details" (attestation).
2. Add an empty `## [Unreleased]` to the changelog.

## After the first release (mandatory, once)

The `nepdate-patro` publisher was registered with a blank environment, so any job of `release.yml`
in this repository could publish it. Narrow it as soon as the project exists:

1. PyPI, `nepdate-patro`, Manage, Publishing: delete the publisher with the blank environment and
   add it again with environment `production`.
2. TestPyPI, the same with environment `testpypi`.
3. Check both project pages list the environment. The next release fails at the patro upload if
   this was done wrong, after the core is already up, so do it before that release, not during it.

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

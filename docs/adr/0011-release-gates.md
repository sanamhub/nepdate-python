# ADR-0011: Release gates and the patro build backend

- Status: Accepted
- Date: 2026-10-18
- Deciders: Sanam Pakuwal
- Amends: ADR-0001 §4 (patro build backend), ADR-0005 (release checks)

## Context

Release rehearsal work added a data freshness rule, a release rehearsal and a local CI matrix. ADR-0005 described
the release checks before they existed and was not edited, since accepted ADRs are immutable.

The patro sdist should carry the `shared/data/patro/*.json` files that `_tables.py` is generated
from. That data lives in the workspace root, outside the patro project. `uv_build` cannot include
files outside the project, and a `source-include` pattern that matches nothing builds an sdist
without the data and without an error. An earlier version worked around this by copying the
repository to a temporary folder and editing the patro `pyproject.toml` before the build, so a
plain `uv build` and the release build gave different sdists.

## Decision

1. The patro project builds with `hatchling` (pinned exactly in `build-system.requires`). Its
   sdist force-includes `../../shared/data/patro` as `shared/data/patro`, and `only-include`
   limits the rest to `src`, `LICENSE`, `NOTICE` and `README.md`. A plain
   `uv build --all-packages` therefore gives the release sdist, and a build without the data
   folder fails instead of dropping it. The wheel is built from `src/nepdate_patro` only; its
   members are the same as the `uv_build` wheel. The core keeps `uv_build`, with
   `source-include` for the calendar data inside its own project.
2. Data freshness: `scripts/data_status.py` reads `shared/data/patro/*.json` and counts days from
   today's UTC date (`--today` overrides it). Public holidays with fewer than 183 days left fail
   the release; tithi and events with fewer than 183 days left print a warning. A missing patro
   folder is a failure, not a skipped check. This is the same rule as the hub and the Rust port,
   and every port uses the UTC date so a release near midnight gets one answer.
3. `scripts/ci.py release-check X.Y.Z` runs in the preflight job without building: both
   `pyproject.toml` versions, the patro dependency range, the dated changelog section and the
   data freshness rule.
4. The build job builds the four files once (`scripts/ci.py build-release`), then
   `scripts/ci.py release-rehearsal X.Y.Z --dist dist` checks those same files: `twine check`
   (pinned in the `release` group), no `tests`, `fuzz` or `docs` path or `test_*.py` file in a
   wheel, `LICENSE`, `NOTICE` and the shared data in each sdist (every patro JSON file by name),
   and the wheel and installed metadata versions. Without `--dist` the rehearsal builds into a
   temporary folder for local use.
5. `scripts/ci_matrix.py` runs `scripts/ci.py` on every Python version in `ci.yml`, read from the
   workflow file. A version uv cannot provide is printed as skipped and never counted as passed.
6. There is no `__version__` attribute. Adding one would be a public addition; the rehearsal
   rejects a stale literal if one is ever added. The ADR-0005 sentence about
   `nepdate.__version__` is superseded.

## Consequences

- One more pinned build dependency (`hatchling`) for the patro distribution, and two build
  backends in one workspace.
- Rebuilding an sdist from an unpacked patro sdist fails, because the force-included path does
  not exist there. Building a wheel from the sdist works, which is what installers do.
- ADR-0005 also lists a post-publish job that installs both versions from PyPI; it does not exist
  yet and is not part of this decision.

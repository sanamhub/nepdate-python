# ADR-0014: The patro requires exactly the same core version

- Status: Accepted
- Date: 2026-11-17
- Deciders: Sanam Pakuwal
- Amends: ADR-0005 and ADR-0011 (the patro dependency range `>=X.Y,<X.(Y+1)`)

## Context

`nepdate-core` and `nepdate-patro` are released together under one version, and the patro reads
internals of the core that are not part of the public API. ADR-0005 let the patro accept any core
of the same minor. A newer patch of the core could then run against an older patro, a pair that was
never tested. The other SDKs already pin their patro package to the exact core version.

## Decision

1. `nepdate-patro` requires `nepdate-core==X.Y.Z` in PEP 440 spelling, for example
   `nepdate-core==1.0.0rc1`. For a pre-release the exact pin names the pre-release, so pip installs
   it without `--pre` for the core.
2. `scripts/versions.py` `core_specifiers` returns that one specifier. Three checks use it:
   `scripts/ci.py version` (the CI `version` job, on every push and pull request),
   the wheel gate in `scripts/ci.py` (it reads the built wheel metadata), and
   `scripts/ci.py release-check`.
3. A version bump changes both `version` fields and the patro dependency in one commit.

## Consequences

- An app that upgrades `nepdate-core` must upgrade `nepdate-patro` to the same version. pip reports
  the conflict.
- Raising the version without the patro pin fails CI at the `version` job.

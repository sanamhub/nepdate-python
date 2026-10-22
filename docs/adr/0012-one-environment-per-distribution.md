# ADR-0012: One publishing environment per distribution

- Status: Accepted
- Date: 2026-10-22
- Deciders: Sanam Pakuwal
- Amends: ADR-0005 (trusted publishers), ADR-0007 §4 (the four pending publishers)

## Context

ADR-0005 and ADR-0007 register four pending trusted publishers: `nepdate-core` and
`nepdate-patro`, on PyPI with environment `production` and on TestPyPI with environment
`testpypi`, and one job uploads both distributions.

PyPI matches a publisher on repository, workflow and environment. Two pending publishers with the
same three values are refused ("A pending trusted publisher matching this configuration has
already been registered for a different project name"). Registering the patro with a blank
environment got past that, but a blank environment matches every job, and the first 0.1.0-beta.1
TestPyPI dry run (run 39675918557) failed at the core upload with "400 Non-user identities cannot
create new projects": TestPyPI had used the patro's pending publisher for the core.

## Decision

Each distribution uploads from its own job and its own GitHub environment:

| Distribution | PyPI environment | TestPyPI environment |
|---|---|---|
| `nepdate-core` | `production` | `testpypi` |
| `nepdate-patro` | `production-patro` | `testpypi-patro` |

The patro job needs the core job, so the core is always uploaded first. Both PyPI jobs check that
the tagged commit is on `origin/main`. `test_release_workflow.py` fails if two upload jobs share an
environment or one job uploads both directories.

## Consequences

- A tag release asks for two approvals, `production` and then `production-patro`.
- No publisher has a wildcard environment, and no post-release step has to narrow one.
- "Re-run failed jobs" after a patro failure re-runs only the patro upload.

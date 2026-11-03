# ADR-0013: Mutation testing on library pull requests

- Status: Accepted
- Date: 2026-11-03
- Deciders: Sanam Pakuwal
- Amends: ADR-0009 (the sentence that gives the mutation workflow no pull-request trigger)

## Context

ADR-0009 put mutation in the release workflow and in a weekly run, and kept it off the pull-request
path because a full run is slow. The weekly run last ran before the API additions of the 0.2 line,
and the next run was the release's own mutation job at the `0.2.0-rc.1` tag. It failed with 39
survivors that no disposition covered, after the tag existed and after the other release gates had
passed.

A survivor is a test gap or a wrong proof, and both are cheaper to find in review than at a tag. A
release can be moved when nothing was published, but the tag, the changelog and the run history
already say the version exists.

## Decision

The mutation workflow also runs on a pull request that changes the library source, its tests, the
mutation checker, the disposition list, the workspace manifests or the workflow itself. A path
filter keeps it off documentation-only and config-only pull requests. The weekly schedule, the
manual dispatch and the release job stay as they are, and the release still blocks on the same
check.

## Consequences

- A pull request that changes `src/nepdate` or `packages/nepdate-patro/src` waits for the mutation
  gate, about four minutes on a Linux runner.
- A survivor is discussed in review, where the test or the proof can be fixed before a tag.
- The floor and the disposition list are still enforced by the release job, so a change that
  bypasses review cannot publish below the floor.

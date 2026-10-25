# Contributing

Thanks for helping. This repository holds the Python `nepdate` library (distribution
`nepdate-core`) and the `nepdate-patro` distribution.

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). Report security problems as
described in [SECURITY.md](SECURITY.md), not in a public issue.

## Before you start

- Open an issue before a new feature or an API change, so we can agree on it first.
- Data and spec problems (a wrong date, holiday or tithi) belong in the hub,
  [`sanamhub/nepdate`](https://github.com/sanamhub/nepdate). `shared/` here is a read-only copy.

## Setup

- [uv](https://docs.astral.sh/uv/) is the only tool you need. `uv sync --all-packages` creates the
  environment from the committed `uv.lock`, on Python 3.11 or newer.

## Making a change

1. Run `uv run --locked python scripts/ci.py` before you open a pull request. It must pass.
2. One change per pull request.
3. Add tests for every behaviour change.
4. Add a changelog line for anything a user would notice.
5. Write an ADR in `docs/adr/` for a significant decision.
6. Use [Conventional Commits](https://www.conventionalcommits.org/), for example
   `feat(nepdate): add serial conversion`.
7. Commit messages and docs: imperative summary, lower case, no trailing period; the body says
   why, not what.

## Generated files

`src/nepdate/_calendar.py` and the `packages/nepdate-patro/LICENSE` and `NOTICE` copies are
generated. Change `scripts/codegen.py` and run `uv run python scripts/codegen.py`. Don't edit the
generated files by hand.

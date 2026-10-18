# ADR-0007: The core distribution name

- Status: Accepted
- Date: 2026-10-18
- Deciders: Sanam Pakuwal
- Amends: ADR-0001 §1, ADR-0005 (the `<core-name>` placeholder)

## Context

ADR-0001 §1 left the core PyPI distribution name to P0-06. The name `nepdate` is taken by a 2021
package with no users worth counting (`docs/competitors.md`, "Name"). P5 prepared 0.1.0 with the
placeholder still in place, and the release cannot register trusted publishers for an unnamed
project.

## Decision

1. The core distribution is **`nepdate-core`**. The import name stays **`nepdate`**.
2. The patro distribution stays **`nepdate-patro`** and depends on
   `nepdate-core>=X.Y,<X.(Y+1)`.
3. The three places that spell the name are the core `[project] name`, the patro `dependencies`
   entry and the patro `[tool.uv.sources]` key. Everything else reads the name from those files:
   `scripts/ci.py`, `sort_dist`, the wheel checks and `release-check`.
4. The four pending publishers in ADR-0005 are `nepdate-core` and `nepdate-patro`, on PyPI
   (environment `production`) and on TestPyPI (environment `testpypi`).

## Consequences

- The install line is `pip install nepdate-core`; the import line is still `from nepdate import
  NepaliDate`.
- The old `nepdate` project on PyPI stays untouched. Installing both it and this package would
  clash on the import name; the old package has no users worth counting, as `docs/competitors.md`
  already says.
- No code change is needed for a later rename: the three pyproject entries and `uv lock` are the
  whole switch.

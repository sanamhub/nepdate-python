# Progress (Python port)

Tasks from [`00-ROADMAP.md`](00-ROADMAP.md), in the format of the hub's `docs/handover.md` §3 step 7.
There is no GitHub remote yet: "CI last line" is `uv run python scripts/ci.py` run locally, and
GitHub-side tasks are blocked on the human.

| Task | Status | Commit | CI last line | Notes and open questions |
|---|---|---|---|---|
| P0-01 | done | 66ed8a5 | `ci: 7/7 gates passed` | uv workspace with the core at the root and `nepdate-patro` as a member. Two wheels and two sdists build; the core wheel has no `Requires-Dist` naming `nepdate-patro`. The lock file is committed. |
| P0-02 | done | 29ab343 | `ci: 7/7 gates passed` | `scripts/codegen.py` validates the 299 years of month lengths (29 to 32), writes `_calendar.py` and the patro `LICENSE`/`NOTICE` copies. `--check` exits 1 on drift; a length of 33 exits non-zero. |
| P0-03 | done | d28e976 | `ci: 7/7 gates passed` | `scripts/ci.py` runs the seven ADR-0004 gates in order and stops at the first failure. Gates 6 and 7 test the built wheels in throwaway venvs. Ruff skips the read-only `shared/` copy. |
| P0-04 | done | 023caa8 | `ci: 7/7 gates passed` | `conftest.py` resolves the repository root from `__file__`, so `uv run pytest` started inside `tests/` still finds `shared/spec/vectors/`. Scripts are loaded with importlib; `_archive_contains` and codegen validation get unit tests. |
| P0-05 | done | 8f8edb1 | `ci: 7/7 gates passed` | `ci.yml` (matrix per ADR-0004 plus 3.14t and the allowed-to-fail 3.15 pre-release, hub `shared-check`), `shared-sync.yml` (weekly), Dependabot, PR and issue templates, `SECURITY.md`, `CONTRIBUTING.md`. Every action pinned by full SHA. Not run on GitHub yet. |
| P0-06 | blocked | | | Human tasks: create `sanamhub/nepdate-python` with branch protection; settle the core distribution name; register the four pending trusted publishers; create the `production` and `testpypi` environments. See "Name" below. |
| P0 checkpoint | ready for review | 8f8edb1 | `ci: 7/7 gates passed` | All five code tasks done; P0-06 is the owner's. Blocked (human): GitHub repository and remote, branch protection, trusted publishers, environments. |

## Name (P0-06)

Checked against the PyPI JSON API on 2026-10-17:

| Name | Status | Evidence |
|---|---|---|
| `nepdate` | taken | Samir Maharjan, "Gets today's nepali date", versions 0.0.2 to 0.0.4, all uploaded 2021-09-22, no repository link |
| `nepdate-bs` | free | 404 from `pypi.org/pypi/nepdate-bs/json` |
| `nepdate-patro` | free | 404 from `pypi.org/pypi/nepdate-patro/json` |
| `pynepdate` | free | 404 from `pypi.org/pypi/pynepdate/json` |
| `nep-date` | free | 404 from `pypi.org/pypi/nep-date/json` |

The core distribution name stays `nepdate` until the owner decides. If the owner picks
`nepdate-bs`, the switch is one place per file: the core `[project] name`, the patro `dependencies`
entry and the patro `[tool.uv.sources]` key. The import name stays `nepdate` either way.

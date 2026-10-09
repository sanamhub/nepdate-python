# AGENTS.md: rules for AI coding agents (Python port)

You are implementing a planned project. Follow the plan; don't redesign it.

## 0. Before writing any code

1. Read `README.md`, this file, every ADR in `docs/adr/`, and `docs/API.md`.
2. Open `docs/plan/00-ROADMAP.md`, find your phase, read that phase file and the spec sections it
   lists under "Read first". Check its preconditions; if one is unmet, stop and say so.

## 1. Sources of truth (in priority order)

1. `shared/spec/*.md` + `shared/spec/vectors/*`: behaviour. Vectors win over prose (report the
   disagreement).
2. `docs/adr/*`: decisions. 3. `docs/plan/*`: tasks and acceptance criteria. 4. `docs/API.md`:
   the public surface (`__all__`).

`shared/` is a read-only copy of the hub. **Never edit it.** A data or spec problem is reported to
the human as a hub issue. Never use the C# NepDate docs as a source (`shared/spec/PARITY.md` §1).

## 2. Hard rules

- Core: no runtime dependency except `tzdata; sys_platform == "win32"`. Patro: only the core.
  Dev tools only in `[dependency-groups]`. Competitor packages only in the `bench` group.
- The core (`src/nepdate/`) never imports, depends on or contains anything from `nepdate_patro`
  (ADR-0001 §5). Patro data lives only in `packages/nepdate-patro/`.
- No public name beyond `docs/API.md` (core and patro). Everything else starts with `_`.
- Never parse JSON or CSV at import time. Tables come from the generated `_calendar.py` and
  `_tables.py`.
- Immutable objects only: `__slots__`, no setters, no module-level mutable state (free-threading).
- Integer maths only; use `divmod` and explicit checks (Python `//` floors, C# truncates). Validate
  arguments with a `type(x) is int` fast path, then reject `bool` and call `operator.index`, so
  `bool` and `float` are rejected (ADR-0002 §2).
- Strict parsing matches ASCII `[0-9]` and the ten Devanagari digits explicitly, never `\d` or
  `str.isdigit()` (they accept every Unicode digit). The one exception is the ASCII fast path of
  P3-04, after `str.isascii()`.
- Performance is the first priority (ADR-0002). Hot paths follow its layout: dates built with
  `_from_parts`, never re-validated; no `bisect`, `divmod` or loop in conversion; no per-call
  object building in `nepdate_patro.info`. Check a change against the ADR-0002 §8 targets with a
  quick `timeit` before calling a phase done.
- Don't edit `src/nepdate/_calendar.py` or `packages/nepdate-patro/src/nepdate_patro/_tables.py`
  by hand. Change `scripts/codegen.py` and run it.
- Parity tests may skip rows **only** for deviations in `shared/spec/PARITY.md`, with a comment
  naming the D-ID. Don't weaken or delete a test to make CI pass.
- No features outside the plan. Secrets never go in code, logs or commits.

## 3. How to work

- One task ID at a time (`P1-03`). Test first, see it fail, then implement.
- Stop at the end of each phase file ("Checkpoint") and wait for the review before the next phase.
- Run `uv run python scripts/ci.py` before saying you're done; paste its last line in the PR.
- PR description: task IDs, what changed and why, how tested, "What to look at first" (2–3 bullets).

## 4. Writing

All prose follows [`.claude/skills/writing-style/SKILL.md`](.claude/skills/writing-style/SKILL.md),
for every agent. Docstrings: one summary line, then what it returns and which exception it raises.
**No AI attribution** in commits or PRs.

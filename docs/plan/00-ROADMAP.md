# Roadmap (Python port)

Each phase is one PR (or a short series), sized so an agent finishes it in one session and a
reviewer reads it in about an hour. Task IDs `P<phase>-<n>`; branch `feat/P1-03-serial`; commit
`feat(nepdate): P1-03 serial conversion` (scope `nepdate-patro` for `packages/nepdate-patro/`).

```
P0 repo + CI ─► P1 core + conversion ─► P2 arithmetic/fiscal/range ─┐
                         └────────────► P3 format + parse ───────────┴─► P4 patro + interop ─► P5 docs, bench, release
```

Preconditions: hub task H0 merged (first `shared/VERSION`; on 2026-10-07 `shared/VERSION` still
reads `pending`, so P0 can't start yet), hub H3 before P0-05, hub H5 (the C# test catalogue)
before P1 ends. P2 and P3 may run in parallel.

| Phase | File | Output |
|---|---|---|
| P0 | [`P0-repo-and-ci.md`](P0-repo-and-ci.md) | uv workspace (core + empty `nepdate-patro`), ruff, mypy, CI script, generator skeleton, community files |
| P1 | [`P1-core-and-conversion.md`](P1-core-and-conversion.md) | `NepaliDate`, enums, errors, generated tables, BS↔AD, `from_date`/`to_date`, ordinals, vectors, exhaustive |
| P2 | [`P2-arithmetic-fiscal-range.md`](P2-arithmetic-fiscal-range.md) | add days/months/years, diff, fiscal year, range, `timedelta` operators |
| P3 | [`P3-format-and-parse.md`](P3-format-and-parse.md) | `short`/`long`/`format`/`__format__`, strict and lenient parse |
| P4 | [`P4-patro-and-interop.md`](P4-patro-and-interop.md) | `nepdate_patro` tables and queries, `today()`, core/patro separation checks |
| P5 | [`P5-docs-bench-release.md`](P5-docs-bench-release.md) | docs, benchmarks vs competitors, release workflow, 0.1.0 of both distributions |
| P6 | [`P6-name-and-import.md`](P6-name-and-import.md) | `nepdate-core` name, import cost, release-from-main guard, competitor miss detail |
| P7 | [`P7-quiet-bench.md`](P7-quiet-bench.md) | quiet-window import and B1 to B8 measurements, C# column, ADR-0008 decision, miss profiles |
| P8 | [`P8-mutation.md`](P8-mutation.md) | mutmut scope and baseline, survivor triage, floor, release and weekly mutation gates |
| P9 | [`P9-fuzz-api.md`](P9-fuzz-api.md) | hypothesis properties with independent oracles, atheris fuzzing, API compatibility gate, dead argument cleanup |
| P10 | [`P10-release-rehearsal.md`](P10-release-rehearsal.md) | local CI matrix from `ci.yml`, patro data freshness gate, release artifact rehearsal, docs drift checks |
| P11 | [`P11-post-publish.md`](P11-post-publish.md) | release notes for 0.1.0, post-publish verification on PyPI and TestPyPI, release runbook |

Every phase file ends with a **Checkpoint** section. The implementation agent stops there, opens
the PR and waits for the reviewer to tick every line before starting the next phase.

## C# test catalogue

`shared/spec/vectors/csharp-tests/catalog.tsv` (hub task H5, in `shared/` since 2026-10-09) lists the
395 `[Fact]` and 147 `[InlineData]` cases of C# NepDate's own tests at `cb05cb65`, each with a
`phase` column (`1` to `4`, `n/a`, or a PARITY deviation `D-xx`). The `phase` column is the
authority. Each phase adds `tests/test_csharp_catalog.py` cases (patro rows in
`packages/nepdate-patro/tests/test_csharp_catalog.py`), one test function per row, named
`test_<id>` with the `id` lower-cased and every character outside `[a-z0-9]` replaced by `_`
(`NepaliDateConstructionTests.Constructor_ValidFormatInvalidDate_ThrowsException#3` becomes
`test_nepalidateconstructiontests_constructor_validformatinvaliddate_throwsexception_3`). A row the port can't express gets a test that
calls `pytest.skip("D-xx: <reason>")` or `pytest.skip("n/a: <C#-only API>")`, so the count stays
checkable. A test in each suite reads the catalogue and fails if a row of its phases has no
function.

Expected spread by C# test file, counted from the clone at `cb05cb65` (Facts + InlineData rows;
the catalogue decides row by row):

| C# test file | Facts + rows | Python phase |
|---|---:|---|
| `Core/NepaliDateConstructionTests`, `Core/NepaliDatePropertiesTests`, `Abilities/NepaliDateComparableTests`, `Core/DictionaryIntegrityTests` | 6+23, 9, 11, 7+4 | P1 |
| `Core/BulkConvertTests`, `Extensions/DateTimeExtensionsTests` | 7, 5 | P1 (a list comprehension stands in for the bulk API) |
| `Core/NepaliDateManipulationTests`, `Core/NepaliDateArithmeticEdgeCaseTests`, `Core/FiscalYearTests`, `Core/FiscalYearInstanceMethodTests`, `Core/NepaliDateRangeTests`, `Core/NepaliDateRangeExtendedTests` | 3+9, 25, 9+2, 38+7, 19, 64 | P2 |
| `Abilities/NepaliDateFormattableTests`, `Abilities/NepaliDateParsableTests`, `Core/NepaliDateMonthNameTests`, `Core/SmartDateParserTests`, `Extensions/StringExtensionsTests` | 20, 5, 3+28, 14, 5 | P3 |
| `Core/CalendarDataTests` | 35 | P4 (tithi, holiday, event rows); P1 (`CalendarOffsets_*` rows) |
| `Core/NepaliDateIsRelativeTests` | 17 | P4 with `today()`; `is_today` and similar are not in `docs/API.md`, so `n/a` unless the catalogue maps them to `today()` comparisons |
| `Core/OptimizationVerificationTests` | 59+74 | mixed P1 to P3, per row |
| `Abilities/NepaliDateTypeConverterTests`, `Serialization/NepaliDateSerializationTests`, `Integration/MemoryUsageTests`, `Integration/MemoryOptimizationBenchmark` | 18, 9, 4, 3 | `n/a` (C#-only APIs; memory is covered by P5-02) |

On top of the catalogue, Python adds: the exhaustive round-trip (P1-05), hypothesis property tests
(ADR-0004), the parse fast-path equivalence test (P3-04), the prebuilt-object `is` tests (P4-02),
and the import-time and core/patro separation gates (ADR-0004 gates 5 to 7).

## Definition of Done (every task)

1. Every acceptance criterion has a test (or a line in the PR saying why it can't).
2. `uv run python scripts/ci.py` passes.
3. No public name beyond `docs/API.md`; no runtime dependency beyond ADR-0001 §5.
4. `CHANGELOG.md` `[Unreleased]` updated for anything a user would notice.
5. Prose follows `.claude/skills/writing-style/SKILL.md`. PR has "What to look at first".

## Milestones

| Milestone | Phases | Exit |
|---|---|---|
| M1 converts | P0–P1 | month-boundary vectors + exhaustive round-trip pass |
| M2 parity | P2–P3 | all C# golden rows pass except `PARITY.md` deviations (golden `parse.tsv` is comparison only, P3-04) |
| M3 0.1.0 | P4–P5 | core and `nepdate-patro` 0.1.0 on PyPI with attestations, benchmark table published |

# nepdate-python

Bikram Sambat (Nepali calendar) for Python. Part of the NepDate family: shared data and spec live
in the hub [`sanamhub/nepdate`](https://github.com/sanamhub/nepdate); the C# original is
[NepDate](https://github.com/RajuPrasai/NepDate).

- Import `nepdate`. The PyPI name `nepdate` is held by an abandoned 2021 package; the
  distribution name is decided in P0-06 (see `docs/competitors.md`, "Name").
- Tithi, public holidays and events (BS 2077-01-01 to 2084-08-20 today) are a separate
  distribution, `nepdate-patro` (import `nepdate_patro`). The core has none of that data.
  Both come from this repository with the same version (ADR-0001).
- Pure Python, zero runtime dependencies (except `tzdata` on Windows, for `today()`), typed
  (`py.typed`), Python 3.11+, works on free-threaded 3.14t.
- BS 1901-01-01 to 2199-12-30 (AD 1844-04-11 to 2143-04-15). Same results as C# NepDate and every
  other port, proved by the shared vectors.

**Status:** planning complete, implementation not started (next: phase P0).

## Where to start

| You are | Read |
|---|---|
| an AI agent implementing a phase | [AGENTS.md](AGENTS.md) → [docs/plan/00-ROADMAP.md](docs/plan/00-ROADMAP.md) |
| reviewing the API | [docs/API.md](docs/API.md) |
| comparing with other Python packages | [docs/competitors.md](docs/competitors.md) |
| wondering "why is it like this?" | [docs/adr/README.md](docs/adr/README.md) |
| looking for the algorithm or data | [shared/spec/README.md](shared/spec/README.md) (changes go to the hub) |

## Layout

```
shared/               hub copy: data/, spec/, VERSION (hub commit)
pyproject.toml        core distribution + uv workspace root
src/nepdate/          core package                    (created in phase P0)
packages/nepdate-patro/
  src/nepdate_patro/ patro package, own pyproject   (skeleton in P0, tables in P4)
  tests/              patro tests
scripts/codegen.py    table generator (standard library only)
benchmarks/           competitor benchmarks, own dependency group (phase P5)
tests/                core tests (pytest + hypothesis)
docs/                 API.md, competitors.md, adr/, plan/, runbooks/
```

## License

MIT ([LICENSE](LICENSE)). Calendar data from NepDate by Raju Prasai and contributors, MIT
([shared/data/NOTICE](shared/data/NOTICE)). Not affiliated with the Government of Nepal.

# Fuzzing

The parsers and the pattern formatter are fuzzed with atheris 3.1.0, a coverage-guided fuzzer
built on libFuzzer. The properties that guard the same entry points are in
[`plan/P9-fuzz-api.md`](plan/P9-fuzz-api.md).

## Targets

| Target | Entry point | Allowed result |
|---|---|---|
| `fuzz/fuzz_parse.py` | `NepaliDate.parse` | A date or `NepDateError` |
| `fuzz/fuzz_parse_lenient.py` | `NepaliDate.parse_lenient` | A date or `NepDateError` |
| `fuzz/fuzz_format.py` | `NepaliDate.format` and `format` | Any string |

Atheris supplies bytes. The harness decodes them with `surrogateescape`, so every byte string
becomes a string and invalid UTF-8 bytes become lone surrogates. The parse targets catch only
`NepDateError`; any other exception fails the target. The format target catches nothing.

## Local run

Atheris runs on Linux and macOS, not Windows. Use WSL Ubuntu:

```console
python3 -m venv /home/sanam/p9-venv
/home/sanam/p9-venv/bin/python -m pip install "atheris==3.1.0"
mkdir -p /mnt/d/devcache/p9/fuzz-artifacts
cd /mnt/e/github/sanamhub/nepdate-python
for target in parse parse_lenient format; do
  PYTHONPATH=src /home/sanam/p9-venv/bin/python "fuzz/fuzz_$target.py" \
    -max_total_time=60 -artifact_prefix=/mnt/d/devcache/p9/fuzz-artifacts/
done
```

The local budget is 60 s per target. Run at most 3 targets at once, and no more than 4 jobs on
the machine. The 2026-10-18 run took 61 s per target and is recorded in
[`fuzz/2026-10-18/summary.json`](fuzz/2026-10-18/summary.json).

No corpus is committed. `fuzz-artifacts/` is ignored. An artifact is committed only when it is a
regression input, and then as a test under `tests/` marked `xfail(strict=True)`, not as a corpus
file.

## Continuous runs

`.github/workflows/fuzz.yml` runs the three targets weekly and by manual dispatch. The release
workflow runs the same matrix, and both publish jobs need it. Each target gets a fixed 300 s
budget. The jobs use `contents: read` and actions pinned by full SHA.

There is no pull-request fuzz job. A crash or a non-`NepDateError` exception is a finding: stop,
commit the failing regression test, and report the input and traceback.

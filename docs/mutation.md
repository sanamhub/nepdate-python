# Mutation testing

The tests are checked by mutmut 3.8.0: it changes one expression at a time and reruns the tests
that cover the changed function. A surviving mutant is either a test gap or a documented
equivalent. The raw baseline is in [`mutation/2026-10-18/`](mutation/2026-10-18/).

## Local run

mutmut 3 needs `fork`, so the local run uses WSL Ubuntu. From a WSL checkout on the same branch:

```console
uv sync --all-packages --group mutation
uv pip uninstall nepdate-core nepdate-patro
cp -r packages/nepdate-patro/src/nepdate_patro src/nepdate_patro
.venv/bin/mutmut run --max-children 4
.venv/bin/mutmut export-cicd-stats
.venv/bin/mutmut results --all true > mutants/results.txt
.venv/bin/python scripts/mutation_check.py mutants/mutmut-cicd-stats.json --results mutants/results.txt
```

The uninstall matters: mutmut puts `mutants/src` first on `sys.path`, but an editable install
otherwise keeps the tests on the unmutated package. The patro copy gives its mutants the
`nepdate_patro` name that the tests import.

At most 4 children. A full run took 313 s with 2 children on 2026-10-18; 4 children is the CI
setting.

## Floor and dispositions

The floor is **91.00 %** of killed over killed plus survived, rounded down from the measured
91.87 %. The first baseline has 1220 killed, 108 survived, 21 timed out and 1 with no tests.
`scripts/mutation_check.py` fails below the floor or when a survivor is missing from
[`mutation/equivalent.md`](mutation/equivalent.md), or when a disposition is stale.

`equivalent.md` has two sections:

- **Equivalent:** the mutant cannot change observable behaviour. An example is `hash(None)` for a
  value type: collisions are allowed and equal values still hash equal.
- **Test-covered:** a named test exercises the behaviour, but mutmut does not attribute the mutant
  to that test. This is labelled as such, not as equivalence.

A new survivor needs one of those two dispositions. "Hard to test" is not a reason.

## Where it runs

- `release.yml` has a `mutation` job; the PyPI and TestPyPI publish jobs need it, so a release
  below the floor cannot publish.
- `.github/workflows/mutation.yml` runs weekly and by manual dispatch. There is no pull-request
  trigger, and `scripts/ci.py` stays at 9 gates.

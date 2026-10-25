"""Which modules ``import nepdate`` loads eagerly and which wait for first use (ADR-0008).

The lenient parser's tables load on the first ``parse_lenient`` call. The formatting modules stay
eager: a call-time ``from ._format import ...`` inside ``__str__`` or ``long`` costs a module
lookup on every call, which took ``str(d)`` from about 210 to 600 ns on the reference machine.

Breaking it: moving ``from ._lenient import ...`` in ``_parse.py`` to module level makes
``test_import_leaves_the_lenient_parser_unloaded`` fail with ``nepdate._lenient`` named.
"""

from __future__ import annotations

import subprocess
import sys

_PROBE = (
    "import sys; import nepdate; "
    "print(','.join(sorted(m for m in sys.modules if m.startswith('nepdate.'))))"
)


def _loaded_after(code: str) -> set[str]:
    """Return the ``nepdate.*`` modules in ``sys.modules`` after ``code`` runs in a new process.

    Args:
        code: Python source that ends by printing the module names, comma separated.

    Returns:
        The module names.
    """
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )
    return set(filter(None, result.stdout.strip().split(",")))


def test_import_leaves_the_lenient_parser_unloaded() -> None:
    """A fresh ``import nepdate`` does not load ``nepdate._lenient``."""
    loaded = _loaded_after(_PROBE)
    assert "nepdate._lenient" not in loaded, sorted(loaded)


def test_import_loads_the_formatting_modules() -> None:
    """``_format`` and ``_pattern`` load with the package, so formatting pays no per-call import."""
    loaded = _loaded_after(_PROBE)
    assert {"nepdate._format", "nepdate._pattern"} <= loaded, sorted(loaded)


def test_first_lenient_parse_loads_the_lenient_parser() -> None:
    """The probe itself can see a lazy module arrive, so the first test is not vacuous."""
    code = _PROBE.replace(
        "import nepdate; ",
        "import nepdate; nepdate.NepaliDate.parse_lenient('15 Shrawan 2080'); ",
    )
    assert "nepdate._lenient" in _loaded_after(code)

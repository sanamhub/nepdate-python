"""The core import must not load ``nepdate_patro`` (P4-02)."""

from __future__ import annotations

import subprocess
import sys


def test_importing_the_core_does_not_load_the_patro() -> None:
    """A subprocess that imports ``nepdate`` has no ``nepdate_patro`` in ``sys.modules``."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import nepdate; print('nepdate_patro' in sys.modules)",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "False"

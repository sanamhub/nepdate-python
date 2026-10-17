"""Source checks for the P3 formatting and parsing rules, and their negative controls."""

from __future__ import annotations

import ast
from pathlib import Path

import nepdate

_FORBIDDEN_CALLS = frozenset({"strftime", "strptime"})
_FORBIDDEN_MODULES = frozenset(
    {"dataclasses", "functools", "locale", "re", "typing", "unicodedata"}
)
_FAST_PATH = "_fast_parse"


def _package_sources() -> dict[str, str]:
    """Return every Python source file of the installed package, keyed by file name."""
    root = Path(nepdate.__file__).resolve().parent
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(root.glob("*.py"))}


def _forbidden(source: str) -> list[str]:
    """Return the forbidden modules and time-formatting calls that ``source`` uses."""
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Attribute) and function.attr in _FORBIDDEN_CALLS:
                found.add(function.attr)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name.split(".")[0]
                if name in _FORBIDDEN_MODULES:
                    found.add(name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            name = node.module.split(".")[0]
            if name in _FORBIDDEN_MODULES:
                found.add(name)
    return sorted(found)


def _isdigit_functions(source: str) -> list[str]:
    """Return the names of the functions that call ``str.isdigit()``."""
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.FunctionDef):
            continue
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr == "isdigit"
            ):
                found.add(node.name)
    return sorted(found)


def _int_functions(source: str) -> list[str]:
    """Return the names of the functions that call ``int()``."""
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.FunctionDef):
            continue
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == "int"
            ):
                found.add(node.name)
    return sorted(found)


def test_no_forbidden_imports_or_time_formatting() -> None:
    """The core imports no forbidden module and calls neither strftime nor strptime."""
    for name, source in _package_sources().items():
        assert not _forbidden(source), f"{name}: {_forbidden(source)}"


def test_only_the_fast_path_uses_isdigit() -> None:
    """``str.isdigit()`` appears only in the ASCII fast path, after ``isascii()``."""
    for name, source in _package_sources().items():
        found = _isdigit_functions(source)
        expected = [_FAST_PATH] if name == "_parse.py" else []
        assert found == expected, f"{name}: {found}"


def test_int_is_only_used_where_ascii_digits_are_known() -> None:
    """``int()`` appears only where the input is known to be ASCII digits."""
    for name, source in _package_sources().items():
        found = _int_functions(source)
        expected = [_FAST_PATH, "_lenient_tokens"] if name == "_parse.py" else []
        assert found == expected, f"{name}: {found}"


def test_forbidden_check_negative_control() -> None:
    """The source check names each forbidden module and time-formatting call it must catch."""
    assert _forbidden("import re\n") == ["re"]
    assert _forbidden("from functools import lru_cache\n") == ["functools"]
    assert _forbidden("import dataclasses\n") == ["dataclasses"]
    assert _forbidden("import typing\n") == ["typing"]
    assert _forbidden("import unicodedata\n") == ["unicodedata"]
    assert _forbidden("import locale\n") == ["locale"]
    assert _forbidden("d.strftime('%Y')\n") == ["strftime"]
    assert _forbidden("d.strptime('x', '%Y')\n") == ["strptime"]
    assert _forbidden("import datetime\nd = datetime.date.today()\n") == []


def test_isdigit_check_negative_control() -> None:
    """The isdigit check flags a call outside the fast path."""
    assert _isdigit_functions("def f(s):\n    return s.isdigit()\n") == ["f"]
    assert _isdigit_functions("def f(s):\n    return s.isascii()\n") == []


def test_int_check_negative_control() -> None:
    """The int check flags a call in any function."""
    assert _int_functions("def f(x):\n    return int(x)\n") == ["f"]
    assert _int_functions("def f(x):\n    return format(x, 'd')\n") == []

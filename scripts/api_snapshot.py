"""Generate and check the committed public API snapshot (P9-03).

The snapshot is generated with ``inspect`` from ``nepdate.__all__`` and
``nepdate_patro.__all__``. It records names, signatures, enum members, class attributes and
exception bases. A removed or changed item fails. An addition passes only when ``docs/API.md``
declares it with a signature, an annotation or an enum value.
"""

from __future__ import annotations

import argparse
import ast
import enum
import inspect
import json
import re
import sys
from pathlib import Path
from typing import Any

import nepdate
import nepdate_patro

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "docs" / "api-snapshot.json"
DOCS = ROOT / "docs" / "API.md"
SCHEMA = 1
_MEMBER_DEPTH = 2
_SKIP_CLASS_NAMES = frozenset(
    {
        "__annotations__",
        "__dict__",
        "__doc__",
        "__module__",
        "__slots__",
        "__weakref__",
    }
)


class ApiError(Exception):
    """Raised when the API cannot be read or checked."""


def _annotation(value: object) -> str:
    """Render a type annotation without module addresses.

    Args:
        value: An annotation from ``inspect`` or a class.

    Returns:
        The annotation text, or an empty string when there is none.
    """
    if value is inspect.Signature.empty or value is inspect.Parameter.empty:
        return ""
    if value is None:
        return "None"
    if isinstance(value, str):
        return value
    if isinstance(value, type):
        return value.__name__
    return str(value)


def _default(value: object) -> str:
    """Render a parameter default, naming enum members by class and member.

    Args:
        value: The default value.

    Returns:
        The default text used in the snapshot.
    """
    if isinstance(value, enum.Enum):
        return f"{type(value).__name__}.{value.name}"
    return repr(value)


def _signature(obj: Any) -> str:
    """Build a stable signature string for a function, method or class.

    Args:
        obj: The callable to inspect.

    Returns:
        The signature, with annotations and defaults in public form.

    Raises:
        ApiError: ``inspect`` cannot read the callable.
    """
    try:
        sig = inspect.signature(obj)
    except (TypeError, ValueError) as exc:
        raise ApiError(f"cannot inspect {obj!r}: {exc}") from exc
    parts: list[str] = []
    keyword_only = False
    for parameter in sig.parameters.values():
        if parameter.kind is inspect.Parameter.KEYWORD_ONLY and not keyword_only:
            parts.append("*")
            keyword_only = True
        prefix = ""
        if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            prefix = "*"
        elif parameter.kind is inspect.Parameter.VAR_KEYWORD:
            prefix = "**"
        text = prefix + parameter.name
        annotation = _annotation(parameter.annotation)
        if annotation:
            text += f": {annotation}"
        if parameter.default is not inspect.Parameter.empty:
            text += f" = {_default(parameter.default)}"
        parts.append(text)
    result = f"({', '.join(parts)})"
    returns = _annotation(sig.return_annotation)
    if returns:
        result += f" -> {returns}"
    return result


def _signature_key(value: str) -> str:
    """Normalise a signature for comparison, ignoring whitespace and quotes."""
    return re.sub(r"\s+", "", value).replace("'", "").replace('"', "")


def _annotation_key(value: str) -> str:
    """Normalise an annotation for comparison, ignoring whitespace and quotes."""
    return _signature_key(value)


def _class_items(key: str, cls: type[Any]) -> dict[str, dict[str, Any]]:  # noqa: PLR0912
    """Build snapshot items for one public class.

    Args:
        key: The qualified key, for example ``nepdate.NepaliDate``.
        cls: The class.

    Returns:
        One item per class, attribute, enum member, property and method.
    """
    is_enum = issubclass(cls, enum.Enum)
    if is_enum:
        kind = "enum"
    elif issubclass(cls, BaseException):
        kind = "exception"
    else:
        kind = "class"
    items: dict[str, dict[str, Any]] = {
        key: {
            "kind": kind,
            "bases": [base.__name__ for base in cls.__bases__],
        }
    }
    if not is_enum:
        items[key]["signature"] = _signature(cls)

    annotations = vars(cls).get("__annotations__", {})
    if isinstance(annotations, dict):
        for name, annotation in annotations.items():
            if not isinstance(name, str) or name.startswith("_"):
                continue
            items[f"{key}.{name}"] = {
                "kind": "attribute",
                "annotation": _annotation(annotation),
            }

    if is_enum:
        for name, member in cls.__members__.items():
            items[f"{key}.{name}"] = {
                "kind": "enum_member",
                "value": repr(member.value),
            }

    for name, raw in vars(cls).items():
        if name in _SKIP_CLASS_NAMES:
            continue
        if name.startswith("_") and not (name.startswith("__") and name.endswith("__")):
            continue
        if is_enum and name == "__new__":
            continue
        if isinstance(raw, property):
            getter = raw.fget
            items[f"{key}.{name}"] = {
                "kind": "property",
                "annotation": _annotation(
                    getter.__annotations__.get("return") if getter is not None else ""
                ),
            }
        elif isinstance(raw, (classmethod, staticmethod)):
            items[f"{key}.{name}"] = {
                "kind": "method",
                "signature": _signature(raw.__func__),
            }
        elif inspect.isfunction(raw):
            items[f"{key}.{name}"] = {
                "kind": "method",
                "signature": _signature(raw),
            }
    return items


def surface() -> dict[str, Any]:
    """Read both public surfaces into one snapshot dictionary.

    Returns:
        The ``schema``, sorted ``all`` names and sorted ``items``.

    Raises:
        ApiError: A name in ``__all__`` is missing or has no supported kind.
    """
    all_names: dict[str, list[str]] = {}
    items: dict[str, dict[str, Any]] = {}
    for module in (nepdate, nepdate_patro):
        names = sorted(getattr(module, "__all__", []))
        all_names[module.__name__] = names
        for name in names:
            key = f"{module.__name__}.{name}"
            try:
                obj = getattr(module, name)
            except AttributeError as exc:
                raise ApiError(f"{module.__name__}.__all__ names missing {name}") from exc
            if inspect.isclass(obj):
                items.update(_class_items(key, obj))
            elif inspect.isfunction(obj):
                items[key] = {"kind": "function", "signature": _signature(obj)}
            else:
                items[key] = {
                    "kind": "constant",
                    "type": type(obj).__name__,
                    "value": repr(obj),
                }
    return {"schema": SCHEMA, "all": all_names, "items": dict(sorted(items.items()))}


def dump(data: dict[str, Any]) -> str:
    """Serialise a snapshot in the committed format.

    Args:
        data: The snapshot dictionary.

    Returns:
        Sorted JSON with a trailing newline.
    """
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _canonical(item: dict[str, Any]) -> dict[str, Any]:
    """Return an item with its signatures normalised for comparison."""
    result = dict(item)
    for field in ("signature", "annotation"):
        value = result.get(field)
        if isinstance(value, str):
            result[field] = _signature_key(value)
    return result


def _items(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return the item table from a snapshot, or raise ``ApiError``."""
    items = data.get("items")
    if not isinstance(items, dict) or not all(
        isinstance(key, str) and isinstance(value, dict) for key, value in items.items()
    ):
        raise ApiError("snapshot has no items table")
    return items


def _code_lines(text: str) -> list[str]:
    """Return the lines inside fenced code blocks in ``docs/API.md``."""
    lines: list[str] = []
    inside = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            inside = not inside
            continue
        if inside:
            lines.append(line)
    return lines


def _parse_members(
    fragment: str, owner: str | None, declarations: dict[str, tuple[str, str]]
) -> None:
    """Record attributes and enum members from one line of API declarations."""
    fragment = fragment.split("#", 1)[0]
    for piece in fragment.split(";"):
        part = piece.strip()
        if not part or part.startswith(("class ", "def ", "from ", "import ", "...")):
            continue
        attribute = re.match(r"^([A-Za-z_]\w*)\s*:\s*(.+)$", part)
        if attribute is not None:
            name, annotation = attribute.groups()
            key = f"{owner}.{name}" if owner else name
            declarations[key] = ("attribute", _annotation_key(annotation))
            continue
        member = re.match(r"^([A-Za-z_]\w*)\s*=\s*(.+)$", part)
        if member is not None:
            name, raw = member.groups()
            key = f"{owner}.{name}" if owner else name
            try:
                value = repr(ast.literal_eval(raw))
            except (SyntaxError, ValueError):
                value = raw.strip()
            declarations[key] = ("enum_member", value)


def _def_block(lines: list[str], start: int) -> tuple[str, int]:
    """Join a possibly multi-line ``def`` declaration and return the next line index."""
    block: list[str] = []
    for index in range(start, len(lines)):
        block.append(lines[index].strip())
        text = " ".join(block)
        close = text.find(")")
        if close >= 0 and text.find(":", close) >= 0:
            return text, index + 1
    return " ".join(block), len(lines)


def _parse_def(text: str) -> tuple[str, str]:
    """Split a joined ``def`` declaration into its name and signature."""
    start = text.find("def ") + len("def ")
    close = text.find(")", start)
    colon = text.find(":", close)
    body = text[start:colon].strip()
    open_paren = body.find("(")
    return body[:open_paren].strip(), body[open_paren:].strip()


def _declarations(text: str) -> dict[str, tuple[str, str]]:
    """Read the declarations from the fenced code blocks of ``docs/API.md``."""
    lines = _code_lines(text)
    declarations: dict[str, tuple[str, str]] = {}
    current: str | None = None
    class_indent = 0
    index = 0
    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()
        if not stripped:
            index += 1
            continue
        indent = len(raw) - len(raw.lstrip())
        class_match = re.match(r"^class\s+(\w+)", stripped)
        if class_match is not None:
            current = class_match.group(1)
            class_indent = indent
            declarations[current] = ("class", "")
            tail = stripped.split(":", 1)[1] if ":" in stripped else ""
            _parse_members(tail, current, declarations)
            index += 1
            continue
        if stripped.startswith("def "):
            if current is not None and indent <= class_indent:
                current = None
            text_block, next_index = _def_block(lines, index)
            name, signature = _parse_def(text_block)
            owner = current if current is not None and indent > class_indent else None
            key = f"{owner}.{name}" if owner else name
            declarations[key] = ("def", _signature_key(signature))
            index = next_index
            continue
        if current is not None and indent > class_indent:
            _parse_members(stripped, current, declarations)
        else:
            current = None
            _parse_members(stripped, None, declarations)
        index += 1
    return declarations


def _local_key(key: str, kind: str) -> str:
    """Map a snapshot key to the key used by the API docs."""
    parts = key.split(".")
    if kind in {"method", "property", "attribute", "enum_member"} and len(parts) >= _MEMBER_DEPTH:
        return ".".join(parts[-2:])
    return parts[-1]


def _check_addition(  # noqa: PLR0911, PLR0912 - one return per API kind
    key: str, item: dict[str, Any], declarations: dict[str, tuple[str, str]]
) -> str | None:
    """Return why an added item is not documented, or None when it is."""
    kind = item.get("kind")
    if not isinstance(kind, str):
        return f"addition has no kind: {key}"
    declaration = declarations.get(_local_key(key, kind))
    if declaration is None:
        return f"undocumented addition: {key}"
    doc_kind, doc_value = declaration
    if kind in {"class", "enum", "exception", "function"}:
        if kind == "function":
            if doc_kind != "def":
                return f"addition is not declared with def: {key}"
            if _signature_key(str(item.get("signature", ""))) != doc_value:
                return f"addition signature differs from docs: {key}"
            return None
        if doc_kind != "class":
            return f"addition is not declared with class: {key}"
        return None
    if kind == "method":
        if doc_kind != "def":
            return f"addition is not declared with def: {key}"
        if _signature_key(str(item.get("signature", ""))) != doc_value:
            return f"addition signature differs from docs: {key}"
        return None
    if kind in {"property", "attribute"}:
        annotation = _annotation_key(str(item.get("annotation", "")))
        if doc_kind == "attribute":
            return None if annotation == doc_value else f"addition annotation differs: {key}"
        if doc_kind == "def":
            expected = _signature_key(f"(self) -> {annotation}")
            return None if expected == doc_value else f"addition signature differs: {key}"
        return f"addition is not declared with an annotation: {key}"
    if kind == "constant":
        if doc_kind != "attribute":
            return f"addition is not declared with an annotation: {key}"
        return (
            None
            if _annotation_key(str(item.get("type", ""))) == doc_value
            else (f"addition type differs from docs: {key}")
        )
    if kind == "enum_member":
        if doc_kind != "enum_member":
            return f"addition is not declared with a value: {key}"
        return (
            None
            if str(item.get("value", "")) == doc_value
            else (f"addition value differs from docs: {key}")
        )
    return f"addition has an unknown kind: {key}"


def compare(old: dict[str, Any], new: dict[str, Any], docs_text: str) -> list[str]:
    """Compare two snapshots and return one message per API problem.

    Args:
        old: The committed snapshot.
        new: The current surface from :func:`surface`.
        docs_text: The contents of ``docs/API.md``.

    Returns:
        One message per removed, changed or undocumented addition.
    """
    old_items = _items(old)
    new_items = _items(new)
    declarations = _declarations(docs_text)
    found: list[str] = []
    for key in sorted(set(old_items) - set(new_items)):
        found.append(f"removed: {key}")
    for key in sorted(set(old_items) & set(new_items)):
        if _canonical(old_items[key]) != _canonical(new_items[key]):
            found.append(f"changed: {key}")
    for key in sorted(set(new_items) - set(old_items)):
        message = _check_addition(key, new_items[key], declarations)
        if message is not None:
            found.append(message)
    return found


def check(snapshot: Path = SNAPSHOT, docs: Path = DOCS) -> list[str]:
    """Read the committed snapshot and return every API problem.

    Args:
        snapshot: The committed JSON snapshot.
        docs: The API documentation.

    Returns:
        One message per problem; an empty list means the surface matches.
    """
    try:
        old = json.loads(snapshot.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read {snapshot}: {exc}"]
    try:
        docs_text = docs.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read {docs}: {exc}"]
    try:
        return compare(old, surface(), docs_text)
    except ApiError as exc:
        return [str(exc)]


def main(argv: list[str] | None = None) -> int:
    """Write or check the committed API snapshot.

    Args:
        argv: Command line arguments. Defaults to ``sys.argv[1:]``.

    Returns:
        0 when the snapshot is written or matches, 1 on a problem, 2 on bad arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="regenerate the snapshot")
    parser.add_argument("--check", action="store_true", help="check the snapshot (the default)")
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--docs", type=Path, default=DOCS)
    args = parser.parse_args(argv)
    if args.write and args.check:
        print("api: choose either --write or --check", file=sys.stderr)
        return 2
    if args.write:
        data = surface()
        args.snapshot.parent.mkdir(parents=True, exist_ok=True)
        args.snapshot.write_text(dump(data), encoding="utf-8", newline="\n")
        print(f"api: wrote {len(data['items'])} items to {args.snapshot}")
        return 0
    problems = check(args.snapshot, args.docs)
    if problems:
        for problem in problems:
            print(f"api: {problem}", file=sys.stderr)
        return 1
    data = json.loads(args.snapshot.read_text(encoding="utf-8"))
    print(f"api: {len(_items(data))} items, snapshot matches")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

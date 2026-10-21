"""The two spellings of a release version: the tag and changelog form, and the PyPI form.

Tags and changelog headings use semver, the same as every other NepDate port (``0.1.0``,
``0.1.0-beta.1``). PyPI needs PEP 440, where the same beta is ``0.1.0b1``. Only the three
pre-release kinds PEP 440 has a short form for are accepted, so the mapping is one to one and
both directions are tested.
"""

from __future__ import annotations

import re

SEMVER = re.compile(
    r"(?P<release>(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*))"
    r"(?:-(?P<kind>alpha|beta|rc)\.(?P<number>0|[1-9][0-9]*))?"
)
PEP440 = re.compile(
    r"(?P<release>(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*))"
    r"(?:(?P<kind>a|b|rc)(?P<number>0|[1-9][0-9]*))?"
)
_TO_PEP440 = {"alpha": "a", "beta": "b", "rc": "rc"}
_TO_SEMVER = {short: long for long, short in _TO_PEP440.items()}


def is_semver(version: str) -> bool:
    """Return whether ``version`` is ``X.Y.Z`` or ``X.Y.Z-(alpha|beta|rc).N``.

    Args:
        version: The tag or changelog version, without a leading ``v``.

    Returns:
        True when the version has one of the accepted shapes.
    """
    return SEMVER.fullmatch(version) is not None


def to_pep440(version: str) -> str:
    """Return the PyPI spelling of a semver release version.

    Args:
        version: ``X.Y.Z`` or ``X.Y.Z-(alpha|beta|rc).N``.

    Returns:
        ``X.Y.Z``, ``X.Y.ZaN``, ``X.Y.ZbN`` or ``X.Y.ZrcN``.

    Raises:
        ValueError: The version has another shape.
    """
    match = SEMVER.fullmatch(version)
    if match is None:
        raise ValueError(f"not a release version: {version}")
    if match["kind"] is None:
        return match["release"]
    return f"{match['release']}{_TO_PEP440[match['kind']]}{match['number']}"


def to_semver(version: str) -> str:
    """Return the tag spelling of a PyPI release version.

    Args:
        version: ``X.Y.Z``, ``X.Y.ZaN``, ``X.Y.ZbN`` or ``X.Y.ZrcN``.

    Returns:
        The semver form, for example ``0.1.0-beta.1`` for ``0.1.0b1``.

    Raises:
        ValueError: The version has another shape.
    """
    match = PEP440.fullmatch(version)
    if match is None:
        raise ValueError(f"not a release version: {version}")
    if match["kind"] is None:
        return match["release"]
    return f"{match['release']}-{_TO_SEMVER[match['kind']]}.{match['number']}"


def is_prerelease(version: str) -> bool:
    """Return whether a semver release version has a pre-release part.

    Args:
        version: A version accepted by :func:`is_semver`.

    Returns:
        True for ``0.1.0-beta.1``, False for ``0.1.0``.
    """
    match = SEMVER.fullmatch(version)
    return match is not None and match["kind"] is not None


def core_specifiers(version: str) -> set[str]:
    """Return the specifiers the patro release must put on the core.

    The upper bound is the next minor, so a patro release never pulls a core with another API.
    For a pre-release the lower bound names the pre-release itself: PEP 440 lets an installer pick
    a pre-release only when a specifier mentions one, so ``>=0.1`` would refuse ``0.1.0b1``.

    Args:
        version: A version accepted by :func:`is_semver`.

    Returns:
        ``{">=X.Y", "<X.(Y+1)"}``, or ``{">=X.Y.ZbN", "<X.(Y+1)"}`` for a pre-release.

    Raises:
        ValueError: The version is not accepted by :func:`is_semver`.
    """
    match = SEMVER.fullmatch(version)
    if match is None:
        raise ValueError(f"not a release version: {version}")
    major, minor, _ = match["release"].split(".")
    lower = f">={major}.{minor}" if match["kind"] is None else f">={to_pep440(version)}"
    return {lower, f"<{major}.{int(minor) + 1}"}

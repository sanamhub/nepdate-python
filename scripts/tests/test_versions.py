"""The tag spelling and the PyPI spelling of a release version map one to one."""

from __future__ import annotations

from typing import Any

import pytest

PAIRS = (
    ("0.1.0", "0.1.0"),
    ("0.1.0-alpha.0", "0.1.0a0"),
    ("0.1.0-beta.1", "0.1.0b1"),
    ("1.2.3-rc.10", "1.2.3rc10"),
)


@pytest.mark.parametrize(("semver", "pep440"), PAIRS)
def test_both_directions(versions: Any, semver: str, pep440: str) -> None:
    """Each tag version has one PyPI spelling, and it maps back."""
    assert versions.to_pep440(semver) == pep440
    assert versions.to_semver(pep440) == semver


@pytest.mark.parametrize(
    "bad",
    [
        "0.1",
        "01.1.0",
        "0.1.0-",
        "0.1.0-beta",
        "0.1.0-beta.01",
        "0.1.0-dev.1",
        "0.1.0+build.1",
        "v0.1.0",
    ],
)
def test_other_shapes_are_rejected(versions: Any, bad: str) -> None:
    """Anything without a one to one PEP 440 form is refused, not guessed."""
    assert not versions.is_semver(bad)
    with pytest.raises(ValueError, match="not a release version"):
        versions.to_pep440(bad)


@pytest.mark.parametrize("bad", ["0.1.0-beta.1", "0.1.0.dev1", "0.1.0b", "0.1.0post1", "0.1"])
def test_pep440_other_shapes_are_rejected(versions: Any, bad: str) -> None:
    """A PyPI version with a dev, post or local part has no tag spelling here."""
    with pytest.raises(ValueError, match="not a release version"):
        versions.to_semver(bad)


def test_prerelease(versions: Any) -> None:
    """Only a version with an alpha, beta or rc part is a pre-release."""
    assert versions.is_prerelease("0.1.0-beta.1")
    assert not versions.is_prerelease("0.1.0")


def test_core_specifiers_follow_the_minor(versions: Any) -> None:
    """A stable patro release accepts any core of the same minor."""
    assert versions.core_specifiers("0.0.0") == {">=0.0", "<0.1"}
    assert versions.core_specifiers("1.4.2") == {">=1.4", "<1.5"}


def test_core_specifiers_name_the_prerelease(versions: Any) -> None:
    """A beta patro release names the beta core, which is what lets pip pick it."""
    assert versions.core_specifiers("0.1.0-beta.1") == {">=0.1.0b1", "<0.2"}


def test_specifiers_admit_the_beta_core_without_pre(versions: Any) -> None:
    """The beta range resolves to the beta core, and the stable range alone would not.

    This is the reason for naming the pre-release in the lower bound: under PEP 440 an installer
    takes a pre-release only when a specifier mentions one.
    """
    from packaging.specifiers import SpecifierSet  # noqa: PLC0415 - test-only dependency

    beta = SpecifierSet(",".join(sorted(versions.core_specifiers("0.1.0-beta.1"))))
    stable = SpecifierSet(",".join(sorted(versions.core_specifiers("0.1.0"))))
    assert "0.1.0b1" in beta
    assert "0.1.0b1" not in stable
    assert "0.2.0b1" not in beta

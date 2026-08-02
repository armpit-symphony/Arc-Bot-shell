"""The reported LIMA trust baseline must be the commit Arc actually installs.

LIMA_PINNED_COMMIT is operator-facing: health.py and integrations/doctor.py
report it, and OperatorConfig validates against it. It drifted behind the
install pin once, because nothing compared the two. These tests compare them.

No commit literals appear here on purpose. Writing one would create exactly
the kind of unregistered duplicate the pin lock exists to prevent.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

import pytest

from arc_bot_shell.lima import LIMA_PINNED_COMMIT, LIMA_SUPERSEDED_COMMITS
from arc_bot_shell.service.config import OperatorConfig


REPO_ROOT = Path(__file__).resolve().parents[1]


def _config(tmp_path: Path, **overrides) -> OperatorConfig:
    values = {
        "install_root": str((tmp_path / "SparkPitLabs" / "ArcBot").resolve()),
        "app_root": str(REPO_ROOT.resolve()),
        "python_executable": str(Path(sys.executable).resolve()),
    }
    values.update(overrides)
    return OperatorConfig(**values)


def test_reported_baseline_is_the_installed_pin() -> None:
    """The cross-check whose absence let the baseline drift."""

    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r"LIMA-AI-OS\.git@([0-9a-f]{40})", pyproject)
    assert match is not None, "pyproject does not pin LIMA by commit"
    assert LIMA_PINNED_COMMIT == match.group(1)


def test_rc1_attestation_uses_the_same_commit() -> None:
    attestation = (
        REPO_ROOT / "tests" / "test_arc_lima_rc1_consumer_pin.py"
    ).read_text(encoding="utf-8")
    match = re.search(r'LIMA_COMMIT = "([0-9a-f]{40})"', attestation)
    assert match is not None
    assert LIMA_PINNED_COMMIT == match.group(1)


def test_windows_installer_reports_the_same_commit() -> None:
    """The installer bakes the baseline into the deployed manifest."""

    common = (REPO_ROOT / "scripts" / "windows" / "common.ps1").read_text(
        encoding="utf-8"
    )
    match = re.search(r'\$script:LimaCommit = "([0-9a-f]{40})"', common)
    assert match is not None
    assert LIMA_PINNED_COMMIT == match.group(1)


def test_superseded_baseline_is_not_the_current_one() -> None:
    assert LIMA_SUPERSEDED_COMMITS
    assert LIMA_PINNED_COMMIT not in LIMA_SUPERSEDED_COMMITS


def test_default_config_uses_the_current_baseline(tmp_path: Path) -> None:
    assert _config(tmp_path).lima_commit == LIMA_PINNED_COMMIT


@pytest.mark.parametrize("superseded", sorted(LIMA_SUPERSEDED_COMMITS))
def test_persisted_config_with_a_superseded_baseline_loads(
    tmp_path: Path, superseded: str
) -> None:
    """An install that predates the correction must keep working."""

    config = _config(tmp_path, lima_commit=superseded)
    assert config.lima_commit == LIMA_PINNED_COMMIT


@pytest.mark.parametrize("superseded", sorted(LIMA_SUPERSEDED_COMMITS))
def test_superseded_baseline_is_normalised_on_disk_round_trip(
    tmp_path: Path, superseded: str
) -> None:
    """Loading an old config must not keep reporting the old commit."""

    written = _config(tmp_path, lima_commit=superseded)
    target = tmp_path / "config.json"
    written.write(target)
    reloaded = OperatorConfig.load(target)

    assert reloaded.lima_commit == LIMA_PINNED_COMMIT
    assert superseded not in target.read_text(encoding="utf-8")


def test_an_unknown_baseline_is_still_rejected(tmp_path: Path) -> None:
    """The migration must not turn the check into a rubber stamp."""

    with pytest.raises(ValueError, match="LIMA commit"):
        _config(tmp_path, lima_commit="b" * 40)

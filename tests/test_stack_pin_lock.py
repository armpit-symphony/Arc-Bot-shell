"""Proofs for the dependency pin lock and the tooling that moves it.

Repeated incidents in this stack came from one pin duplicated across several
files with only some copies updated. These tests hold both halves: this
repository must be consistent right now, and each way of breaking it must
actually be caught.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest


ROOT = Path(__file__).resolve().parents[1]
_HELPER = ROOT / "scripts" / "stack_pins.py"
_spec = importlib.util.spec_from_file_location("stack_pins", _HELPER)
assert _spec is not None and _spec.loader is not None
stack_pins = importlib.util.module_from_spec(_spec)
sys.modules["stack_pins"] = stack_pins
_spec.loader.exec_module(stack_pins)

CHECKER = ROOT / "scripts" / "check-stack-pins.py"

COMMIT_A = "1111111111111111111111111111111111111111"
COMMIT_B = "2222222222222222222222222222222222222222"


def _fixture_lock(commit: str = COMMIT_A, policy: str = "tracking") -> dict:
    return {
        "lock_version": "1.0.0",
        "dependencies": {
            "demo-dep": {
                "repo": "armpit-symphony/Demo",
                "commit": commit,
                "policy": policy,
                "reason": "held for a documented reason" if policy == "frozen" else "",
                "package": None,
                "sites": [
                    {
                        "path": "requirements-demo.txt",
                        "pattern": "Demo\\.git@(?P<commit>[0-9a-f]{40})",
                        "occurrences": 1,
                    },
                    {
                        "path": "docs/DEMO.md",
                        "pattern": "Demo dep:\\s*`(?P<commit>[0-9a-f]{40})`",
                        "occurrences": 1,
                    },
                ],
            }
        },
    }


def _write_fixture(root: Path, lock: dict, commit: str = COMMIT_A) -> None:
    (root / "docs").mkdir(parents=True, exist_ok=True)
    with open(root / "stack.lock.json", "w", encoding="utf-8", newline="\n") as handle:
        json.dump(lock, handle, indent=2)
        handle.write("\n")
    # Deliberately CRLF: a bumper that normalises line endings would rewrite the
    # whole file instead of the one pin it was asked to move.
    with open(
        root / "requirements-demo.txt", "w", encoding="utf-8", newline=""
    ) as handle:
        handle.write(
            f"demo-dep @ git+https://github.com/armpit-symphony/Demo.git@{commit}\r\n"
        )
    with open(root / "docs" / "DEMO.md", "w", encoding="utf-8", newline="") as handle:
        handle.write(f"# Demo\n\n- Demo dep:\n  `{commit}`\n")


def _fixture_repo(root: Path, lock: dict) -> None:
    _write_fixture(root, lock)
    (root / "scripts").mkdir(exist_ok=True)
    for name in ("stack_pins.py", "bump-pin.py"):
        (root / "scripts" / name).write_bytes((ROOT / "scripts" / name).read_bytes())


# --- this repository, right now -------------------------------------------


def test_lock_parses_and_declares_every_pinned_dependency() -> None:
    lock = stack_pins.load_lock(ROOT)
    names = {dependency.name for dependency in lock.dependencies}
    assert names == {"lima-runtime", "guardian-suite", "lima-adapter-trust-baseline"}


def test_every_site_agrees_with_the_lock() -> None:
    lock = stack_pins.load_lock(ROOT)
    assert stack_pins.check_sites(lock, ROOT) == []


def test_checker_passes_on_this_repository() -> None:
    result = subprocess.run(
        [sys.executable, str(CHECKER)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Result: PASS" in result.stdout
    assert "is not registered" not in result.stdout


def test_install_pin_is_repeated_in_all_five_sites() -> None:
    """pyproject, both lock entries, the README, and the RC1 attestation."""

    dependency = stack_pins.load_lock(ROOT).dependency("lima-runtime")
    paths = sorted(site.path for site in dependency.sites)
    assert paths == [
        "README.md",
        "pyproject.toml",
        "tests/test_arc_lima_rc1_consumer_pin.py",
        "workspace.lock.json",
        "workspace.lock.json",
    ]


def test_lima_pin_is_frozen_with_a_reason() -> None:
    """The RC1 API freeze is deliberate, so tooling must not 'fix' it."""

    dependency = stack_pins.load_lock(ROOT).dependency("lima-runtime")
    assert dependency.policy == "frozen"
    assert "RC1" in dependency.reason


def test_adapter_trust_baseline_divergence_stays_declared() -> None:
    """LIMA_PINNED_COMMIT does not match the install pin, and that is recorded.

    It is reported by health and doctor and validated by the operator config,
    so correcting it is a migration rather than a bump. This test fails if the
    divergence is closed or moved without revisiting the recorded reason.
    """

    lock = stack_pins.load_lock(ROOT)
    baseline = lock.dependency("lima-adapter-trust-baseline")
    install = lock.dependency("lima-runtime")
    assert baseline.policy == "frozen"
    assert baseline.commit != install.commit
    assert "KNOWN DIVERGENCE" in baseline.reason


def test_evidence_records_are_not_tracked_as_pins() -> None:
    """Proof packets and fixtures are history and must stay untouched."""

    lock = stack_pins.load_lock(ROOT)
    for dependency in lock.dependencies:
        for site in dependency.sites:
            assert not site.path.startswith("docs/proof_packets/")
            assert not site.path.startswith("docs/audits/")
            assert not site.path.startswith("tests/fixtures/")


# --- lock validation -------------------------------------------------------


def _load_mutated(mutate) -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        lock = _fixture_lock()
        mutate(lock)
        _write_fixture(root, lock)
        stack_pins.load_lock(root)


def test_frozen_pin_requires_a_reason() -> None:
    def mutate(lock):
        lock["dependencies"]["demo-dep"]["policy"] = "frozen"
        lock["dependencies"]["demo-dep"]["reason"] = "   "

    with pytest.raises(stack_pins.LockError, match="why it is held behind main"):
        _load_mutated(mutate)


def test_unknown_policy_is_rejected() -> None:
    with pytest.raises(stack_pins.LockError):
        _load_mutated(
            lambda lock: lock["dependencies"]["demo-dep"].update(policy="whatever")
        )


@pytest.mark.parametrize("bad", ["1111111", "a" * 41, ("ab" * 20).upper()])
def test_malformed_commit_is_rejected(bad: str) -> None:
    with pytest.raises(stack_pins.LockError):
        _load_mutated(lambda lock: lock["dependencies"]["demo-dep"].update(commit=bad))


def test_pattern_without_a_commit_group_is_rejected() -> None:
    def mutate(lock):
        lock["dependencies"]["demo-dep"]["sites"][0]["pattern"] = "[0-9a-f]{40}"

    with pytest.raises(stack_pins.LockError, match="named 'commit'"):
        _load_mutated(mutate)


def test_dependency_without_sites_is_rejected() -> None:
    with pytest.raises(stack_pins.LockError):
        _load_mutated(lambda lock: lock["dependencies"]["demo-dep"].update(sites=[]))


def test_operational_paths_default_when_absent(tmp_path: Path) -> None:
    _write_fixture(tmp_path, _fixture_lock())
    lock = stack_pins.load_lock(tmp_path)
    assert lock.operational_paths == stack_pins.DEFAULT_OPERATIONAL_PATHS


def test_operational_paths_can_be_declared(tmp_path: Path) -> None:
    raw = _fixture_lock()
    raw["operational_paths"] = ["pyproject.toml"]
    _write_fixture(tmp_path, raw)
    assert stack_pins.load_lock(tmp_path).operational_paths == ("pyproject.toml",)


# --- drift detection -------------------------------------------------------


def test_a_site_left_behind_is_reported(tmp_path: Path) -> None:
    _write_fixture(tmp_path, _fixture_lock())
    target = tmp_path / "requirements-demo.txt"
    target.write_bytes(
        target.read_bytes().replace(COMMIT_A.encode(), COMMIT_B.encode())
    )
    failures = stack_pins.check_sites(stack_pins.load_lock(tmp_path), tmp_path)
    assert len(failures) == 1
    assert "requirements-demo.txt" in failures[0]
    assert COMMIT_B in failures[0]


def test_a_missing_site_is_reported(tmp_path: Path) -> None:
    _write_fixture(tmp_path, _fixture_lock())
    (tmp_path / "docs" / "DEMO.md").unlink()
    failures = stack_pins.check_sites(stack_pins.load_lock(tmp_path), tmp_path)
    assert len(failures) == 1
    assert "does not exist" in failures[0]


def test_an_extra_occurrence_is_reported(tmp_path: Path) -> None:
    _write_fixture(tmp_path, _fixture_lock())
    with open(
        tmp_path / "requirements-demo.txt", "a", encoding="utf-8", newline=""
    ) as handle:
        handle.write(f"other @ git+https://github.com/x/Demo.git@{COMMIT_A}\r\n")
    failures = stack_pins.check_sites(stack_pins.load_lock(tmp_path), tmp_path)
    assert len(failures) == 1
    assert "matched 2 occurrence" in failures[0]


# --- rewriting -------------------------------------------------------------


def test_rewrite_replaces_only_the_captured_commit() -> None:
    site = stack_pins.Site(
        path="x", pattern="Demo\\.git@(?P<commit>[0-9a-f]{40})", occurrences=1
    )
    text = f"prefix Demo.git@{COMMIT_A} suffix {COMMIT_A}"
    assert stack_pins.rewrite_site(text, site, COMMIT_B) == (
        f"prefix Demo.git@{COMMIT_B} suffix {COMMIT_A}"
    )


def test_bump_moves_the_lock_and_every_site(tmp_path: Path) -> None:
    _fixture_repo(tmp_path, _fixture_lock())
    result = subprocess.run(
        [sys.executable, str(tmp_path / "scripts" / "bump-pin.py"),
         "demo-dep", "--to", COMMIT_B],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    lock = stack_pins.load_lock(tmp_path)
    assert lock.dependency("demo-dep").commit == COMMIT_B
    assert stack_pins.check_sites(lock, tmp_path) == []


def test_bump_preserves_crlf_line_endings(tmp_path: Path) -> None:
    _fixture_repo(tmp_path, _fixture_lock())
    before = (tmp_path / "requirements-demo.txt").read_bytes()
    assert b"\r\n" in before

    subprocess.run(
        [sys.executable, str(tmp_path / "scripts" / "bump-pin.py"),
         "demo-dep", "--to", COMMIT_B],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        check=True,
    )
    after = (tmp_path / "requirements-demo.txt").read_bytes()
    assert after == before.replace(COMMIT_A.encode(), COMMIT_B.encode())
    assert after.count(b"\r\n") == before.count(b"\r\n")


def test_bump_refuses_a_frozen_pin_without_force(tmp_path: Path) -> None:
    _fixture_repo(tmp_path, _fixture_lock(policy="frozen"))
    result = subprocess.run(
        [sys.executable, str(tmp_path / "scripts" / "bump-pin.py"),
         "demo-dep", "--to", COMMIT_B],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )
    assert result.returncode == 0, result.stderr
    assert "skipped" in result.stdout
    assert stack_pins.load_lock(tmp_path).dependency("demo-dep").commit == COMMIT_A


def test_forced_bump_moves_a_frozen_pin(tmp_path: Path) -> None:
    _fixture_repo(tmp_path, _fixture_lock(policy="frozen"))
    subprocess.run(
        [sys.executable, str(tmp_path / "scripts" / "bump-pin.py"),
         "demo-dep", "--to", COMMIT_B, "--force"],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        check=True,
    )
    assert stack_pins.load_lock(tmp_path).dependency("demo-dep").commit == COMMIT_B

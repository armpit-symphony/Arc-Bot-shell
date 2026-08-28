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
    assert names == {
        "lima-runtime",
        "guardian-suite",
        "arc-rollback-target",
        "lima-superseded-operator-baseline",
    }


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


def test_install_pin_is_repeated_in_all_nine_sites() -> None:
    """Including the adapter baseline and the Windows installer chain."""

    dependency = stack_pins.load_lock(ROOT).dependency("lima-runtime")
    paths = sorted(site.path for site in dependency.sites)
    assert paths == [
        "README.md",
        "arc_bot_shell/lima/lima_runtime_adapter.py",
        "pyproject.toml",
        "scripts/windows/common.ps1",
        "scripts/windows/smoke-arc-windows-operator.ps1",
        "tests/test_arc_lima_rc1_consumer_pin.py",
        "tests/test_arc_windows_operator_v0_11.py",
        "workspace.lock.json",
        "workspace.lock.json",
    ]


def test_lima_pin_is_frozen_with_a_reason() -> None:
    """The coordinated preview freeze is deliberate, not routine currency."""

    dependency = stack_pins.load_lock(ROOT).dependency("lima-runtime")
    assert dependency.policy == "frozen"
    assert "Lab Preview coherence freeze" in dependency.reason


def test_currency_checker_defuses_disposable_git_cleanup_race() -> None:
    """Scheduled currency checks must not fail after Git already succeeded."""

    source = CHECKER.read_text(encoding="utf-8")
    assert "maintenance.auto=false" in source
    assert "ignore_cleanup_errors=True" in source


def test_operator_trust_baseline_is_a_site_of_the_install_pin() -> None:
    """The adapter baseline and the install pin are now one fact.

    They diverged because they were two independent constants that nothing
    compared. Holding the adapter constant as a site of lima-runtime makes a
    future divergence a build failure rather than a discovery.
    """

    dependency = stack_pins.load_lock(ROOT).dependency("lima-runtime")
    paths = {site.path for site in dependency.sites}
    assert "arc_bot_shell/lima/lima_runtime_adapter.py" in paths


def test_superseded_baseline_is_registered_but_never_current() -> None:
    """The retired baseline is kept only to migrate old operator configs."""

    lock = stack_pins.load_lock(ROOT)
    superseded = lock.dependency("lima-superseded-operator-baseline")
    assert superseded.policy == "frozen"
    assert superseded.commit != lock.dependency("lima-runtime").commit
    assert "never be bumped" in superseded.reason


def test_rollback_target_agrees_across_config_installer_and_smoke() -> None:
    """A rollback that restores a different commit in each place is a hazard."""

    dependency = stack_pins.load_lock(ROOT).dependency("arc-rollback-target")
    assert len(dependency.sites) == 4
    assert dependency.policy == "frozen"


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


# --- the interpreter, not just the files ----------------------------------
#
# Every site can agree and the interpreter can still be importing a different
# commit. Isolated repository environments keep that mismatch visible even
# while the coordinated preview currently selects one shared runtime commit.


def _fake_dist(
    site: Path,
    name: str,
    version: str = "0.1.0rc1",
    direct_url: dict | None = None,
) -> None:
    """Write a distribution importlib.metadata will discover on sys.path."""

    dist_info = site / f"{name.replace('-', '_')}-{version}.dist-info"
    dist_info.mkdir(parents=True, exist_ok=True)
    (dist_info / "METADATA").write_text(
        f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n",
        encoding="utf-8",
    )
    if direct_url is not None:
        (dist_info / "direct_url.json").write_text(
            json.dumps(direct_url), encoding="utf-8"
        )


def _vcs(commit: str, requested: str | None = None) -> dict:
    return {
        "url": "https://github.com/armpit-symphony/LIMA-AI-OS.git",
        "vcs_info": {
            "vcs": "git",
            "commit_id": commit,
            "requested_revision": commit if requested is None else requested,
        },
    }


@pytest.fixture
def site(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    directory = tmp_path / "site-packages"
    directory.mkdir()
    monkeypatch.syspath_prepend(str(directory))
    importlib.invalidate_caches()
    return directory


def test_a_vcs_install_reports_the_commit_pip_resolved(site: Path) -> None:
    _fake_dist(site, "demo-pkg", direct_url=_vcs(COMMIT_A))
    found = stack_pins.installed_package("demo-pkg")
    assert found is not None
    assert found.commit == COMMIT_A


def test_a_package_that_is_absent_reports_nothing(site: Path) -> None:
    assert stack_pins.installed_package("demo-pkg-never-installed") is None


def test_a_moving_ref_is_distinguishable_from_a_pinned_commit(site: Path) -> None:
    """An install asking for @main can resolve right and still be unpinned."""

    _fake_dist(site, "demo-pkg", direct_url=_vcs(COMMIT_A, requested="main"))
    found = stack_pins.installed_package("demo-pkg")
    assert found is not None
    assert found.commit == COMMIT_A
    assert found.requested_revision == "main"


def test_a_local_checkout_is_not_treated_as_a_verified_commit(site: Path) -> None:
    """An editable install can contain anything; it must not pass as a pin."""

    _fake_dist(
        site,
        "demo-pkg",
        direct_url={"url": "file:///C:/work/LIMA-AI-OS", "dir_info": {"editable": True}},
    )
    found = stack_pins.installed_package("demo-pkg")
    assert found is not None
    assert found.commit is None
    assert "local checkout" in found.described_origin


def test_a_registry_install_has_no_commit_to_verify(site: Path) -> None:
    _fake_dist(site, "demo-pkg")
    found = stack_pins.installed_package("demo-pkg")
    assert found is not None
    assert found.commit is None


def test_unreadable_provenance_is_reported_rather_than_raised(site: Path) -> None:
    dist_info = site / "demo_pkg-0.1.0rc1.dist-info"
    _fake_dist(site, "demo-pkg", direct_url=_vcs(COMMIT_A))
    (dist_info / "direct_url.json").write_text("{not json", encoding="utf-8")
    found = stack_pins.installed_package("demo-pkg")
    assert found is not None
    assert found.commit is None


def test_a_commit_that_is_not_a_full_lowercase_hash_is_refused(site: Path) -> None:
    """The same shape rule the lock enforces, applied to what pip recorded."""

    _fake_dist(site, "demo-pkg", direct_url=_vcs("ABCDEF1234"))
    found = stack_pins.installed_package("demo-pkg")
    assert found is not None
    assert found.commit is None


def _installed_fixture(root: Path, commit: str = COMMIT_A) -> None:
    lock = _fixture_lock(commit=commit)
    lock["dependencies"]["demo-dep"]["package"] = {
        "name": "demo-pkg",
        "version": "0.1.0rc1",
    }
    _write_fixture(root, lock, commit=commit)
    (root / "scripts").mkdir(exist_ok=True)
    for name in ("stack_pins.py", "check-stack-pins.py"):
        (root / "scripts" / name).write_bytes((ROOT / "scripts" / name).read_bytes())


def _run_checker(root: Path, site: Path, *flags: str) -> subprocess.CompletedProcess:
    import os

    env = dict(os.environ)
    env["PYTHONPATH"] = str(site)
    return subprocess.run(
        [sys.executable, str(root / "scripts" / "check-stack-pins.py"), *flags],
        capture_output=True,
        text=True,
        cwd=str(root),
        env=env,
    )


def test_the_wrong_interpreter_fails_and_names_both_commits(tmp_path: Path) -> None:
    """The failure this exists to catch, reported so the cause is obvious."""

    site = tmp_path / "site-packages"
    site.mkdir()
    _fake_dist(site, "demo-pkg", direct_url=_vcs(COMMIT_B))
    _installed_fixture(tmp_path, commit=COMMIT_A)

    result = _run_checker(tmp_path, site, "--check-installed")

    assert result.returncode == 1, result.stdout
    assert "Result: FAIL" in result.stdout
    assert COMMIT_A[:7] in result.stdout
    assert COMMIT_B[:7] in result.stdout
    # Without the interpreter path the operator cannot tell which environment
    # is at fault, which is the whole question when two repositories disagree.
    assert sys.executable in result.stdout


def test_the_matching_interpreter_passes(tmp_path: Path) -> None:
    site = tmp_path / "site-packages"
    site.mkdir()
    _fake_dist(site, "demo-pkg", direct_url=_vcs(COMMIT_A))
    _installed_fixture(tmp_path, commit=COMMIT_A)

    result = _run_checker(tmp_path, site, "--check-installed")

    assert result.returncode == 0, result.stdout
    assert "Result: PASS" in result.stdout


def test_a_missing_package_fails_rather_than_passing_quietly(tmp_path: Path) -> None:
    site = tmp_path / "site-packages"
    site.mkdir()
    _installed_fixture(tmp_path, commit=COMMIT_A)

    result = _run_checker(tmp_path, site, "--check-installed")

    assert result.returncode == 1, result.stdout
    assert "is not installed" in result.stdout


def test_the_default_run_still_ignores_the_environment(tmp_path: Path) -> None:
    """Consistency must stay offline and environment-independent."""

    site = tmp_path / "site-packages"
    site.mkdir()
    _fake_dist(site, "demo-pkg", direct_url=_vcs(COMMIT_B))
    _installed_fixture(tmp_path, commit=COMMIT_A)

    result = _run_checker(tmp_path, site)

    assert result.returncode == 0, result.stdout
    assert "installation checked: no" in result.stdout


def test_this_repository_declares_lima_runtime_as_an_installable_package() -> None:
    """Dropping the package block would silently make the check a no-op."""

    dependency = stack_pins.load_lock(ROOT).dependency("lima-runtime")
    assert dependency.package_name == "lima-runtime"

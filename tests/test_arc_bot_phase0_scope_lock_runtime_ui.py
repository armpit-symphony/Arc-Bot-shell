"""Phase-0 scope lock checks for runtime UI scaffold."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_arc_bot_scope_lock_documentation_exists() -> None:
    roadmap_path = REPO_ROOT / "docs" / "ROADMAP.md"
    foundation_path = REPO_ROOT / "docs" / "OPERATOR_CONSOLE_FOUNDATION.md"
    readme_path = REPO_ROOT / "README.md"

    roadmap = roadmap_path.read_text(encoding="utf-8")
    foundation = foundation_path.read_text(encoding="utf-8")
    readme = readme_path.read_text(encoding="utf-8")

    assert roadmap_path.exists()
    assert "Phase-0 Roadmap" in roadmap
    assert "1) Scope Lock (Runtime UI Scaffold)" in roadmap
    assert "1.2 Guardian spine/suite seam plan for Phase-1+" in roadmap
    assert "app.services.guardian.suite" in roadmap
    assert "guardian_spine_tasks" in roadmap
    assert "1.4 Contract-shape scaffolding" in roadmap
    assert "No live model calls" in roadmap
    assert "LIMA-Guardian-Suite" in roadmap

    assert "Phase 0 Scope Lock (Runtime UI Scaffold)" in foundation
    assert "This branch defines a runtime UI scaffold only." in foundation
    assert "Guardian/Suite Alignment (Display Only)" in foundation
    assert "No worker dispatch or task execution." in foundation
    assert "guardian_spine_events" in foundation

    assert "docs/ROADMAP.md" in readme
    assert "phase-0 runtime ui scaffold is locked" in readme.lower()
    assert "LIMA-Guardian-Suite" in readme
    assert "python -m phase0_runtime_ui_scaffold.preview" in readme

"""Foundation planning/documentation presence checks."""

from __future__ import annotations

from pathlib import Path


def test_arc_bot_foundation_documents_exist() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    required = (
        "ARCHITECTURE.md",
        "MVP_SCOPE.md",
        "CONTRACTS.md",
        "SECURITY_MODEL.md",
        "THREAT_MODEL.md",
        "WORKER_NODE_SPEC.md",
        "SUPERVISOR_SPEC.md",
        "AUTONOMY_BOUNDARIES.md",
        "DECISIONS.md",
        "OPEN_QUESTIONS.md",
    )

    for filename in required:
        path = repo_root / filename
        assert path.exists(), f"Missing required foundation document: {filename}"
        assert path.read_text(encoding="utf-8").strip(), f"Empty foundation document: {filename}"

"""Evidence bundle creation for Arc Harness Shell runs."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from arc_bot_shell.contracts import EvidenceBundle, GuardianDecision


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def default_evidence_dir(repo_root: Path) -> Path:
    return repo_root / "artifacts" / "evidence"


def build_evidence_bundle(
    *,
    run_id: str,
    action_id: str,
    task_ref: str,
    guardian_decision: GuardianDecision,
    runtime_adapter: str,
    result_status: str,
    blocked_reason: str | None,
) -> EvidenceBundle:
    timestamp = _utc_now()
    return EvidenceBundle(
        run_id=run_id,
        action_id=action_id,
        task_ref=task_ref,
        guardian_decision_id=guardian_decision.decision_id,
        guardian_status=guardian_decision.status,
        runtime_adapter=runtime_adapter,
        result_status=result_status,
        blocked_reason=blocked_reason,
        created_at=timestamp,
        updated_at=timestamp,
        redaction_metadata={
            "status": "placeholder",
            "policy_ref": "redaction://arc-harness-shell/v0.1",
            "contains_secrets": False,
        },
    )


def write_evidence_bundle(bundle: EvidenceBundle, evidence_dir: Path) -> Path:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / f"{bundle.run_id}.json"
    evidence_path.write_text(
        json.dumps(bundle.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return evidence_path

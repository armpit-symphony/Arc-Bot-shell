"""Evidence bundle creation for Arc Harness Shell runs."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from arc_bot_shell.contracts import EvidenceBundle, GuardianDecision, ModelPreviewResult


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
    model_preview: ModelPreviewResult | None = None,
    lima_called: bool = False,
    ollama_called: bool = False,
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
        model_preview=(None if model_preview is None else model_preview.to_dict()),
        guardian={
            "adapter": guardian_decision.metadata.get(
                "guardian_adapter", guardian_decision.evaluator
            ),
            "import_path": guardian_decision.metadata.get("guardian_import_path"),
            "decision_id": guardian_decision.decision_id,
            "status": guardian_decision.metadata.get(
                "guardian_status", guardian_decision.status
            ),
            "allowed": guardian_decision.allowed,
            "requires_approval": guardian_decision.requires_approval,
            "reason": guardian_decision.reason,
            "requested_action": guardian_decision.requested_action,
            "risk_level": guardian_decision.risk_level,
            "policy_name": guardian_decision.policy_name,
            "created_at": guardian_decision.created_at,
            "guardian_contract_reference": guardian_decision.metadata.get(
                "guardian_contract_reference"
            ),
        },
        lima_called=lima_called,
        ollama_called=ollama_called,
    )


def write_evidence_bundle(bundle: EvidenceBundle, evidence_dir: Path) -> Path:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / f"{bundle.run_id}.json"
    evidence_path.write_text(
        json.dumps(bundle.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return evidence_path

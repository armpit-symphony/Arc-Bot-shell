"""Structured contracts for the Arc Harness Shell runtime path."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal


ARC_SAFE_HARNESS_ACTIONS = (
    "arc.noop",
    "arc.classify_task_packet",
    "arc.preview_operator_response",
    "arc.local_model_preview",
    "arc.generate_evidence_packet",
    "arc.mark_task_blocked",
)

ARC_GUARDIAN_STATUSES = (
    "allowed_preview_only",
    "blocked",
    "requires_operator_approval",
)

ARC_BLOCK_CATEGORIES = (
    "external_send",
    "file_write",
    "network_action",
    "device_action",
    "robotics_action",
    "credential_access",
    "office_system_mutation",
)

ArcHarnessAction = Literal[
    "arc.noop",
    "arc.classify_task_packet",
    "arc.preview_operator_response",
    "arc.local_model_preview",
    "arc.generate_evidence_packet",
    "arc.mark_task_blocked",
]
GuardianStatus = Literal[
    "allowed_preview_only",
    "blocked",
    "requires_operator_approval",
]
BlockCategory = Literal[
    "external_send",
    "file_write",
    "network_action",
    "device_action",
    "robotics_action",
    "credential_access",
    "office_system_mutation",
]


class ArcActionRequestError(ValueError):
    """Raised when a task packet cannot be parsed into an Arc action request."""


@dataclass(frozen=True)
class ArcActionRequest:
    """Operator-visible Arc harness request with no hidden side effects."""

    action_id: str
    task_ref: str
    action_name: ArcHarnessAction
    summary: str
    preview_only: bool = True
    requires_operator_approval: bool = False
    operator_id: str = "operator-local"
    worker_id: str = "arc-worker-001"
    tenant_id: str = "single-tenant-local"
    requested_capabilities: tuple[str, ...] = ()
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ArcActionRequest":
        if not isinstance(raw, dict):
            raise ArcActionRequestError("task packet must be a JSON object")
        missing = [
            field_name
            for field_name in ("action_id", "task_ref", "action_name", "summary")
            if not raw.get(field_name)
        ]
        if missing:
            raise ArcActionRequestError(
                f"task packet is missing required fields: {', '.join(missing)}"
            )
        action_name = str(raw["action_name"])
        if action_name not in ARC_SAFE_HARNESS_ACTIONS:
            raise ArcActionRequestError(
                f"unsupported harness action {action_name!r}; expected one of {ARC_SAFE_HARNESS_ACTIONS}"
            )
        requested_capabilities = raw.get("requested_capabilities", ())
        if not isinstance(requested_capabilities, (list, tuple)):
            raise ArcActionRequestError("requested_capabilities must be a list")
        payload = raw.get("payload", {})
        if not isinstance(payload, dict):
            raise ArcActionRequestError("payload must be an object")
        return cls(
            action_id=str(raw["action_id"]),
            task_ref=str(raw["task_ref"]),
            action_name=action_name,  # type: ignore[arg-type]
            summary=str(raw["summary"]),
            preview_only=bool(raw.get("preview_only", True)),
            requires_operator_approval=bool(raw.get("requires_operator_approval", False)),
            operator_id=str(raw.get("operator_id", "operator-local")),
            worker_id=str(raw.get("worker_id", "arc-worker-001")),
            tenant_id=str(raw.get("tenant_id", "single-tenant-local")),
            requested_capabilities=tuple(str(item) for item in requested_capabilities),
            payload=payload,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GuardianDecision:
    """Guardian evaluation output for one Arc request."""

    decision_id: str
    action_id: str
    status: GuardianStatus
    evaluator: str
    reason: str
    block_category: BlockCategory | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LimaRuntimeResult:
    """Result from a LIMA runtime port call."""

    runtime_adapter: str
    result_status: str
    output: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModelPreviewResult:
    """Result from a local model preview adapter call."""

    adapter_name: str
    model_name: str
    prompt_summary: str
    draft_text: str
    used_network: bool
    used_credentials: bool
    status: str
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceBundle:
    """Local evidence record for one harness run."""

    run_id: str
    action_id: str
    task_ref: str
    guardian_decision_id: str
    guardian_status: GuardianStatus
    runtime_adapter: str
    result_status: str
    blocked_reason: str | None
    created_at: str
    updated_at: str
    redaction_metadata: dict[str, Any]
    model_preview: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HarnessRunResult:
    """CLI-facing Arc harness result."""

    run_id: str
    action_id: str
    task_ref: str
    guardian_decision: GuardianDecision
    runtime_adapter: str
    runtime_called: bool
    result_status: str
    blocked_reason: str | None
    evidence_path: Path
    exit_code: int
    model_preview_called: bool = False
    model_preview: dict[str, Any] | None = None
    runtime_output: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence_path"] = str(self.evidence_path)
        return payload

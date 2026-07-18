"""Arc Harness Shell v0.8 real Guardian adapter tests."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from arc_bot_shell.approvals import JsonlApprovalStore
from arc_bot_shell.guardian import (
    GuardianCoreAdapter,
    GuardianCoreAdapterError,
    GuardianFacade,
    StrictUnavailableGuardian,
    build_guardian_policy_context,
)
from arc_bot_shell.harness import load_task_packet, run_task_packet
from arc_bot_shell.health import build_health_report
from arc_bot_shell.integrations import (
    DoctorConfig,
    DoctorProbes,
    GuardianContractProbe,
    LimaContractProbe,
    OllamaProbeResult,
    run_doctor,
)
from arc_bot_shell.state import JsonlStateStore
from arc_bot_shell.tasks import intake_task, run_queued_task

REPO_ROOT = Path(__file__).resolve().parents[1]
GUARDIAN_ROOT = REPO_ROOT.parent / "LIMA-Guardian-Suite"
LOCAL_PREVIEW = REPO_ROOT / "samples" / "tasks" / "local_model_preview.json"
EXTERNAL_EMAIL = REPO_ROOT / "samples" / "tasks" / "external_email_send.json"


@dataclass(frozen=True)
class FakeGuardianRequest:
    requested_action: str
    arguments: Mapping[str, Any]
    policy_context: Mapping[str, Any]
    actor_id: str | None = None
    task_ref: str | None = None
    source: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FakePublicDecision:
    decision_id: str
    status: str
    allowed: bool
    requires_approval: bool
    reason: str
    requested_action: str
    risk_level: str | None = "low"
    policy_name: str | None = "guardian_core.policy"
    created_at: str = "2026-07-16T00:00:00Z"
    metadata: Mapping[str, Any] = field(
        default_factory=lambda: {
            "execution_performed": False,
            "external_services_called": False,
        }
    )


class ContractEvaluator:
    def __init__(
        self,
        *,
        status: str = "allow",
        decision_ids: list[str] | None = None,
    ) -> None:
        self.status = status
        self.decision_ids = list(decision_ids or ["guardian-decision:test-v0-8"])
        self.requests: list[FakeGuardianRequest] = []

    def __call__(self, request: FakeGuardianRequest) -> FakePublicDecision:
        self.requests.append(request)
        status = self.status
        if request.requested_action != "arc.local_model_preview":
            status = "deny"
        if request.arguments.get("endpoint") not in {
            "http://127.0.0.1:11434",
            "http://localhost:11434",
        }:
            status = "deny"
        expected_context = {
            "network_scope": "loopback_only",
            "external_side_effects": False,
            "credentials_required": False,
            "execution_scope": "model_preview_only",
            "runtime_route": "lima",
        }
        if dict(request.policy_context) != expected_context:
            status = "deny"
        decision_id = self.decision_ids.pop(0)
        return FakePublicDecision(
            decision_id=decision_id,
            status=status,
            allowed=status == "allow",
            requires_approval=status == "requires_approval",
            reason=f"contract-faithful {status}",
            requested_action=request.requested_action,
        )


def _adapter(
    evaluator: ContractEvaluator,
    *,
    endpoint: str = "http://127.0.0.1:11434",
) -> GuardianCoreAdapter:
    return GuardianCoreAdapter(
        endpoint=endpoint,
        contract_loader=lambda _path: (
            FakeGuardianRequest,
            FakePublicDecision,
            evaluator,
            "fake-install/guardian_core/__init__.py",
        ),
    )


def _facade(adapter: GuardianCoreAdapter) -> GuardianFacade:
    return GuardianFacade(
        primary=adapter,
        fallback=StrictUnavailableGuardian(),
    )


class ExplodingRuntime:
    adapter_name = "exploding-runtime"

    def invoke(self, *_args: object, **_kwargs: object) -> object:
        raise AssertionError("LIMA runtime must not be called in v0.8")


class ExplodingModel:
    adapter_name = "exploding-model"
    model_name = "exploding-model"

    def preview(self, *_args: object, **_kwargs: object) -> object:
        raise AssertionError("Ollama/model adapter must not be called in v0.8")


def test_adapter_uses_only_guardian_package_public_imports() -> None:
    path = REPO_ROOT / "arc_bot_shell" / "guardian" / "guardian_core_adapter.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    guardian_imports = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and (node.module or "").startswith("guardian_core")
    ]

    assert len(guardian_imports) == 1
    assert guardian_imports[0].module == "guardian_core"
    assert {alias.name for alias in guardian_imports[0].names} == {
        "GuardianEvaluationRequest",
        "GuardianDecision",
        "evaluate_guardian_request",
    }


def test_health_reports_supported_guardian_public_entrypoint(tmp_path: Path) -> None:
    report = build_health_report(repo_root=tmp_path)

    assert report["guardian"]["public_entrypoint"] == "guardian_core"


def test_local_preview_maps_exact_bounded_guardian_request() -> None:
    evaluator = ContractEvaluator()
    request = load_task_packet(LOCAL_PREVIEW)

    decision = _adapter(evaluator).evaluate(
        request,
        policy_context=build_guardian_policy_context(request),
    )
    observed = evaluator.requests[0]

    assert decision.decision_id == "guardian-decision:test-v0-8"
    assert observed.requested_action == "arc.local_model_preview"
    assert observed.arguments == {
        "model_adapter": "ollama",
        "endpoint": "http://127.0.0.1:11434",
    }
    assert observed.policy_context == {
        "network_scope": "loopback_only",
        "external_side_effects": False,
        "credentials_required": False,
        "execution_scope": "model_preview_only",
        "runtime_route": "lima",
    }
    assert observed.actor_id == request.operator_id
    assert observed.task_ref == request.task_ref
    assert observed.source == "arc_bot_shell"
    assert observed.metadata == {
        "action_id": request.action_id,
        "worker_id": request.worker_id,
        "tenant_id": request.tenant_id,
    }


def test_two_guardian_decisions_preserve_separate_ids() -> None:
    evaluator = ContractEvaluator(
        decision_ids=[
            "guardian-decision:first",
            "guardian-decision:second",
        ]
    )
    adapter = _adapter(evaluator)
    request = load_task_packet(LOCAL_PREVIEW)

    first = adapter.evaluate(
        request, policy_context=build_guardian_policy_context(request)
    )
    second = adapter.evaluate(
        request, policy_context=build_guardian_policy_context(request)
    )

    assert first.decision_id == "guardian-decision:first"
    assert second.decision_id == "guardian-decision:second"


def test_guardian_allow_writes_same_lineage_and_stops_before_execution(
    tmp_path: Path,
) -> None:
    decision_id = "guardian-decision:allow-lineage"
    evaluator = ContractEvaluator(decision_ids=[decision_id])
    state_path = tmp_path / "state" / "runs.jsonl"

    result = run_task_packet(
        LOCAL_PREVIEW,
        runtime_name="disabled",
        evidence_dir=tmp_path / "evidence",
        state_path=state_path,
        guardian_facade=_facade(_adapter(evaluator)),
        runtime_port=ExplodingRuntime(),  # type: ignore[arg-type]
        model_preview_adapter=ExplodingModel(),  # type: ignore[arg-type]
    )
    evidence = json.loads(result.evidence_path.read_text(encoding="utf-8"))
    state = JsonlStateStore(state_path).list_runs()[0]

    assert result.result_status == "guardian_approved_for_lima"
    assert result.guardian_decision_id == decision_id
    assert result.eligible_for_lima is True
    assert result.runtime_called is False
    assert result.model_preview_called is False
    assert result.lima_called is False
    assert result.ollama_called is False
    assert evidence["guardian"]["decision_id"] == decision_id
    assert evidence["guardian"]["status"] == "allow"
    assert evidence["lima_called"] is False
    assert evidence["ollama_called"] is False
    assert state.guardian_decision_id == decision_id
    assert state.guardian_status == "allow"
    assert state.eligible_for_lima is True
    assert state.runtime_called is False
    assert state.model_preview_called is False
    assert state.lima_called is False
    assert state.ollama_called is False


def test_guardian_deny_blocks_runtime_model_and_preserves_reason(
    tmp_path: Path,
) -> None:
    evaluator = ContractEvaluator(
        status="deny",
        decision_ids=["guardian-decision:deny-lineage"],
    )

    result = run_task_packet(
        LOCAL_PREVIEW,
        runtime_name="disabled",
        evidence_dir=tmp_path / "evidence",
        state_path=tmp_path / "state.jsonl",
        guardian_facade=_facade(_adapter(evaluator)),
        runtime_port=ExplodingRuntime(),  # type: ignore[arg-type]
        model_preview_adapter=ExplodingModel(),  # type: ignore[arg-type]
    )

    assert result.result_status == "blocked"
    assert result.guardian_decision_id == "guardian-decision:deny-lineage"
    assert result.blocked_reason == "contract-faithful deny"
    assert result.runtime_called is False
    assert result.model_preview_called is False


def test_remote_ollama_endpoint_is_denied_without_execution(tmp_path: Path) -> None:
    evaluator = ContractEvaluator(decision_ids=["guardian-decision:remote-deny"])

    result = run_task_packet(
        LOCAL_PREVIEW,
        runtime_name="disabled",
        evidence_dir=tmp_path / "evidence",
        state_path=tmp_path / "state.jsonl",
        guardian_facade=_facade(
            _adapter(evaluator, endpoint="http://192.168.1.20:11434")
        ),
        runtime_port=ExplodingRuntime(),  # type: ignore[arg-type]
        model_preview_adapter=ExplodingModel(),  # type: ignore[arg-type]
    )

    assert result.guardian_status == "deny"
    assert result.eligible_for_lima is False
    assert result.runtime_called is False
    assert result.model_preview_called is False


def test_external_email_remains_denied(tmp_path: Path) -> None:
    evaluator = ContractEvaluator(decision_ids=["guardian-decision:external-deny"])

    result = run_task_packet(
        EXTERNAL_EMAIL,
        runtime_name="disabled",
        evidence_dir=tmp_path / "evidence",
        state_path=tmp_path / "state.jsonl",
        guardian_facade=_facade(_adapter(evaluator)),
        runtime_port=ExplodingRuntime(),  # type: ignore[arg-type]
        model_preview_adapter=ExplodingModel(),  # type: ignore[arg-type]
    )

    assert result.guardian_status == "deny"
    assert result.guardian_decision_id == "guardian-decision:external-deny"
    assert result.runtime_called is False
    assert result.model_preview_called is False


def test_requires_approval_creates_record_without_execution(
    tmp_path: Path,
) -> None:
    task_path = tmp_path / "approval.json"
    task_path.write_text(LOCAL_PREVIEW.read_text(encoding="utf-8"), encoding="utf-8")
    queue_path = tmp_path / "tasks.jsonl"
    approval_path = tmp_path / "approvals.jsonl"
    record = intake_task(task_path, queue_path=queue_path)
    evaluator = ContractEvaluator(
        status="requires_approval",
        decision_ids=["guardian-decision:approval-lineage"],
    )

    task, result, exit_code = run_queued_task(
        record.task_id,
        queue_path=queue_path,
        runtime_name="disabled",
        evidence_dir=tmp_path / "evidence",
        state_path=tmp_path / "state.jsonl",
        approval_path=approval_path,
        repo_root=tmp_path,
        guardian_facade=_facade(_adapter(evaluator)),
        stop_after_guardian=True,
    )
    approval = JsonlApprovalStore(approval_path).list_approvals()[0]

    assert result is not None
    assert exit_code == 3
    assert task.latest_approval_id == approval.approval_id
    assert approval.guardian_decision_id == "guardian-decision:approval-lineage"
    assert approval.execution_allowed is False
    assert result.runtime_called is False
    assert result.model_preview_called is False


def test_missing_guardian_fails_closed_without_forged_decision_id(
    tmp_path: Path,
) -> None:
    def missing(_path: Path | None):
        raise GuardianCoreAdapterError("guardian_core unavailable")

    adapter = GuardianCoreAdapter(contract_loader=missing)
    result = run_task_packet(
        LOCAL_PREVIEW,
        runtime_name="disabled",
        evidence_dir=tmp_path / "evidence",
        state_path=tmp_path / "state.jsonl",
        guardian_facade=_facade(adapter),
    )

    assert result.result_status == "blocked"
    assert result.guardian_decision_id == ""
    assert result.runtime_called is False
    assert result.model_preview_called is False


def test_guardian_contract_mismatch_fails_closed(tmp_path: Path) -> None:
    def evaluator(_request: object) -> object:
        return object()

    adapter = GuardianCoreAdapter(
        contract_loader=lambda _path: (
            FakeGuardianRequest,
            FakePublicDecision,
            evaluator,
            "fake-install/guardian_core/__init__.py",
        )
    )

    result = run_task_packet(
        LOCAL_PREVIEW,
        runtime_name="disabled",
        evidence_dir=tmp_path / "evidence",
        state_path=tmp_path / "state.jsonl",
        guardian_facade=_facade(adapter),
    )

    assert result.result_status == "blocked"
    assert result.guardian_decision_id == ""
    assert "incompatible decision type" in (result.blocked_reason or "")


def test_doctor_reports_real_guardian_policy_support_without_runtime() -> None:
    guardian = GuardianContractProbe(
        available=True,
        mode="guardian_core",
        import_path="guardian_core",
        evaluation_entrypoint="guardian_core.evaluate_guardian_request",
        request_input_type="guardian_core.GuardianEvaluationRequest",
        decision_output_type="guardian_core.GuardianDecision",
        decision_id_field="decision_id",
        requires_sparkbot_imports=False,
        integration_compatible=True,
        contract_compatible=True,
        decision_id_supported=True,
        local_preview_policy_supported=True,
        policy_reference="guardian-core-v1.1-local-model-preview-policy",
    )
    missing_lima = LimaContractProbe(
        available=False,
        import_path=None,
        runtime_entrypoint=None,
        runtime_input_type=None,
        runtime_output_type=None,
        provider_executor_interface=None,
        guardian_request_type=None,
        guardian_decision_type=None,
        decision_id_field=None,
        requires_sparkbot_imports=None,
        integration_compatible=False,
        blockers=("ARC_LIMA_PATH_not_configured",),
    )
    report = run_doctor(
        DoctorConfig(
            lima_path=None,
            guardian_path=None,
            ollama_url=None,
            ollama_model=None,
            guardian_mode="guardian_core",
        ),
        DoctorProbes(
            guardian=lambda _path: guardian,
            lima=lambda _path: missing_lima,
            ollama=lambda _url, _model, _timeout: OllamaProbeResult(False, False),
        ),
    )

    assert report["guardian_available"] is True
    assert report["guardian_contract_compatible"] is True
    assert report["guardian_decision_id_supported"] is True
    assert report["local_preview_policy_supported"] is True
    assert report["real_guardian_ready"] is True
    assert report["local_integration_ready"] is False


@pytest.mark.skipif(
    not (GUARDIAN_ROOT / "guardian_core" / "__init__.py").is_file(),
    reason="local Guardian checkout is unavailable",
)
def test_real_local_guardian_checkout_preserves_decision_id(
    tmp_path: Path,
) -> None:
    result = run_task_packet(
        LOCAL_PREVIEW,
        runtime_name="disabled",
        evidence_dir=tmp_path / "evidence",
        state_path=tmp_path / "state.jsonl",
        guardian_mode="guardian_core",
        guardian_path=GUARDIAN_ROOT,
        stop_after_guardian=True,
    )
    evidence = json.loads(result.evidence_path.read_text(encoding="utf-8"))
    state = JsonlStateStore(tmp_path / "state.jsonl").list_runs()[0]

    assert result.guardian_decision_id.startswith("guardian-decision:")
    assert evidence["guardian"]["decision_id"] == result.guardian_decision_id
    assert state.guardian_decision_id == result.guardian_decision_id
    assert result.result_status == "guardian_approved_for_lima"
    assert result.runtime_called is False
    assert result.model_preview_called is False
    assert result.ollama_called is False

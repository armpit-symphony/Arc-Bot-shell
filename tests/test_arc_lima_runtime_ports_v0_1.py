"""LIMA runtime port tests for Arc Harness Shell v0.1."""

from __future__ import annotations

from pathlib import Path

from arc_bot_shell.contracts import ArcActionRequest
from arc_bot_shell.guardian import TestFakeGuardian
from arc_bot_shell.harness import run_task_packet
from arc_bot_shell.lima import FakeLimaRuntimePort, LocalLimaImportRuntimePort


def _request(**overrides: object) -> ArcActionRequest:
    payload = {
        "action_id": "arc-action-runtime-001",
        "task_ref": "task://tests/runtime-001",
        "action_name": "arc.preview_operator_response",
        "summary": "Preview a safe runtime response.",
        "preview_only": True,
        "requested_capabilities": [],
        "payload": {"ticket_id": "T-001"},
    }
    payload.update(overrides)
    return ArcActionRequest.from_dict(payload)


def test_arc_action_request_maps_to_lima_runtime_input() -> None:
    request = _request()
    decision = TestFakeGuardian().evaluate(request)
    runtime = LocalLimaImportRuntimePort(repo_root=Path(__file__).resolve().parents[1])

    payload = runtime.build_runtime_input(request, decision)

    assert payload["input_id"] == request.action_id
    assert payload["consumer"] == "arc_bot_shell"
    assert payload["requested_action"] == "arc.preview_operator_response"
    assert payload["metadata"]["guardian_status"] == "allowed_preview_only"
    assert payload["metadata"]["requested_capabilities"] == []


def test_fake_runtime_execution_is_deterministic() -> None:
    request = _request()
    decision = TestFakeGuardian().evaluate(request)
    runtime = FakeLimaRuntimePort()

    result = runtime.invoke(request, decision)

    assert result.runtime_adapter == "fake"
    assert result.result_status == "preview_completed"
    assert result.output["guardian_status"] == "allowed_preview_only"
    assert "Preview ready" in result.output["preview_text"]


def test_blocked_action_does_not_call_runtime(tmp_path: Path) -> None:
    class ExplodingRuntime:
        adapter_name = "exploding"

        def invoke(self, request: ArcActionRequest, decision: object) -> object:
            raise AssertionError("runtime should not be invoked for blocked actions")

    task_path = tmp_path / "blocked.json"
    task_path.write_text(
        """{
  "action_id": "arc-action-runtime-002",
  "task_ref": "task://tests/runtime-002",
  "action_name": "arc.preview_operator_response",
  "summary": "Attempt an external send.",
  "preview_only": true,
  "requested_capabilities": ["external_send"],
  "payload": {}
}
""",
        encoding="utf-8",
    )

    result = run_task_packet(
        task_path,
        runtime_name="fake",
        evidence_dir=tmp_path / "evidence",
        guardian_facade=None,
        runtime_port=ExplodingRuntime(),
    )

    assert result.runtime_called is False
    assert result.result_status == "blocked"
    assert result.exit_code == 2

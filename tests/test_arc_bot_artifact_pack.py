"""Arc Bot artifact pack tests."""

from __future__ import annotations

from scripts.emit_arc_bot_artifacts import build_arc_bot_artifact_pack


def test_artifact_pack_includes_remaining_gate_response_intake() -> None:
    pack = build_arc_bot_artifact_pack()
    artifacts = pack["artifacts"]

    response_intake = artifacts["phase_d_remaining_gate_response_intake"]
    assert response_intake["artifact_type"] == "arc_remaining_implementation_gate_response_projection"
    assert response_intake["status"] == "response_shape_complete_runtime_still_blocked"
    assert response_intake["response_shape_complete"] is True
    assert response_intake["runtime_authority_blocked"] is True
    assert response_intake["runtime_execution_blocked"] is True
    assert response_intake["unresolved_external_dependencies"] == []

"""Arc intent envelope contract tests."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from arc_guardian_spine import ArcActionRequest
from arc_guardian_spine.intent_envelope import (
    ArcIntentEnvelope,
    ArcIntentEnvelopeError,
    build_arc_intent_envelope,
    build_arc_intent_envelope_projection,
    validate_arc_intent_envelope,
)


def test_arc_intent_envelope_projection_is_read_only_and_blocked() -> None:
    projection = build_arc_intent_envelope_projection()

    assert projection["artifact_type"] == "arc_intent_envelope_projection"
    assert projection["phase"] == "phase-2-contract"
    assert projection["projection_scope"] == "planning_read_only"
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["handoff_requirements"]["signature_verification_required"] is True
    assert projection["handoff_requirements"]["execution_allowed"] is False

    envelope = projection["envelope"]
    assert envelope["signature_ref"] == "signature://guardian-lima-office/pending"
    assert envelope["signature_verified_by_arc_shell"] is False
    assert envelope["requires_guardian_verification"] is True


def test_arc_intent_envelope_requires_signature_reference() -> None:
    request = ArcActionRequest(
        action_id="arc-action-envelope-test",
        action_kind="document_intake_preview",
    )

    with pytest.raises(ArcIntentEnvelopeError):
        build_arc_intent_envelope(
            request,
            signature_ref="",
            signature_status="missing",
        )


def test_arc_intent_envelope_rejects_runtime_authority() -> None:
    request = ArcActionRequest(
        action_id="arc-action-envelope-test",
        action_kind="document_intake_preview",
    )
    envelope = ArcIntentEnvelope(
        envelope_id="arc-intent-envelope:test",
        action_request=request,
        signature_ref="signature://guardian-lima-office/pending",
        runtime_authority_blocked=False,
    )

    with pytest.raises(ArcIntentEnvelopeError):
        validate_arc_intent_envelope(envelope)


def test_arc_intent_envelope_rejects_arc_shell_signature_verification_claim() -> None:
    request = ArcActionRequest(
        action_id="arc-action-envelope-test",
        action_kind="document_intake_preview",
    )
    envelope = ArcIntentEnvelope(
        envelope_id="arc-intent-envelope:test",
        action_request=request,
        signature_ref="signature://guardian-lima-office/pending",
        signature_verified_by_arc_shell=True,
    )

    with pytest.raises(ArcIntentEnvelopeError):
        validate_arc_intent_envelope(envelope)


def test_arc_intent_envelope_preview_cli_outputs_projection() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "arc_guardian_spine.intent_envelope_preview",
            "--action-kind",
            "document_extract_preview",
            "--requested-tool-pack",
            "local_model_preview",
            "--compact",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    projection = json.loads(result.stdout)

    assert projection["artifact_type"] == "arc_intent_envelope_projection"
    assert projection["guardian_decision_preview"]["decision"] == "approval_required"
    assert projection["runtime_execution_blocked"] is True

"""Phase-1 business/runtime alignment remains read-only and blocked."""

from __future__ import annotations

import io
import json
from unittest.mock import patch

from phase1_business_shell_inventory.runtime_alignment import (
    build_phase1_business_runtime_alignment_projection,
    run_phase1_business_runtime_alignment_preview,
)


def test_phase1_business_runtime_alignment_projection_is_blocked() -> None:
    projection = build_phase1_business_runtime_alignment_projection()

    assert projection["artifact_type"] == "phase1_business_runtime_alignment_projection"
    assert projection["phase"] == "phase-1"
    assert projection["projection_scope"] == "planning_read_only"
    assert projection["source_access_mode"] == "read_only"
    assert projection["runtime_authority_blocked"] is True
    assert projection["runtime_execution_blocked"] is True
    assert projection["alignment_posture"] == "blocked_until_guardian_lima_office_runtime_gate"
    assert projection["role_bindings"] == [
        "billing_assistant_bot",
        "it_helpdesk_frontline",
        "office_manager_bot",
    ]
    assert projection["unresolved_required_gates"]


def test_phase1_business_runtime_alignment_cli_compact_output() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_phase1_business_runtime_alignment_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_type"] == "phase1_business_runtime_alignment_projection"
    assert parsed["runtime_execution_blocked"] is True

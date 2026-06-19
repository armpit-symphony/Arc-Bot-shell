"""Full preview-chain CLI and projection smoke tests."""

from __future__ import annotations

import io
import json
from unittest.mock import patch

from phase0_runtime_ui_scaffold.phase_chain import (
    build_phase0_runtime_ui_scaffold_chain,
    run_phase_chain_preview,
)


def test_build_phase_chain_projection() -> None:
    chain = build_phase0_runtime_ui_scaffold_chain()

    assert chain["artifact_type"] == "phase0_runtime_ui_scaffold_phase_chain_projection"
    assert chain["phase"] == "phase-1"
    assert chain["projection_scope"] == "read_only"
    assert chain["source_access_mode"] == "read_only"
    assert chain["runtime_authority_blocked"] is True
    assert chain["runtime_execution_blocked"] is True
    assert "phase_markers" in chain

    phases = chain["phases"]
    assert set(phases.keys()) == {
        "phase1_read_feed_contract",
        "phase1_read_feed_runtime",
        "phase1_runtime_consumer",
        "phase2_control",
        "phase2_control_consumer",
    }
    assert phases["phase1_read_feed_contract"]["phase"] == "phase-1"
    assert phases["phase2_control_consumer"]["runtime_execution_blocked"] is True


def test_run_phase_chain_preview_cli_compact() -> None:
    output = io.StringIO()
    with patch("sys.stdout", output):
        status = run_phase_chain_preview(["--compact"])

    assert status == 0
    parsed = json.loads(output.getvalue())
    assert parsed["artifact_type"] == "phase0_runtime_ui_scaffold_phase_chain_projection"
    assert parsed["phase_markers"]["execution_mode"] == "disabled"

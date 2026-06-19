"""End-to-end phase seam validation for the runtime UI scaffold."""

from __future__ import annotations

from phase0_runtime_ui_scaffold.phase2_runtime_control import build_phase2_runtime_control_projection
from phase0_runtime_ui_scaffold.read_feed import (
    DEFAULT_CONTRACT_PATH,
    build_phase1_read_feed_projection,
    build_phase1_read_feed_runtime_projection,
)
from phase0_runtime_ui_scaffold.runtime_control_consumer import (
    build_phase2_runtime_control_consumer_projection,
)
from phase0_runtime_ui_scaffold.runtime_consumer import (
    build_phase1_runtime_ui_consumer_projection,
)


def test_runtime_ui_scaffold_phase_chain_is_consistent_and_blocked() -> None:
    phase1_projection_contract = build_phase1_read_feed_projection(DEFAULT_CONTRACT_PATH)
    phase1_runtime_projection = build_phase1_read_feed_runtime_projection()
    phase1_consumer_projection = build_phase1_runtime_ui_consumer_projection()
    phase2_control_projection = build_phase2_runtime_control_projection()
    phase2_control_consumer_projection = build_phase2_runtime_control_consumer_projection()

    assert phase1_projection_contract["projection_scope"] == "read_only"
    assert phase1_projection_contract["phase"] == "phase-1"
    assert phase1_runtime_projection["phase"] == "phase-1"
    assert phase1_runtime_projection["projection_scope"] == "read_only"
    assert phase1_runtime_projection["source_access_mode"] == "read_only"

    assert phase1_consumer_projection["phase"] == "phase-1"
    assert phase1_consumer_projection["projection_scope"] == "read_only"
    assert phase1_consumer_projection["source_access_mode"] == "read_only"
    assert phase1_consumer_projection["runtime_authority_blocked"] is True

    assert phase2_control_projection["phase"] == "phase-1"
    assert phase2_control_projection["projection_source"] == "phase1_runtime_ui_consumer_projection"
    assert phase2_control_projection["runtime_authority_blocked"] is True
    assert phase2_control_projection["projection_bindings"] == phase1_consumer_projection["spine_sources"]

    assert (
        phase2_control_consumer_projection["projection_source"]
        == "phase2_runtime_control_handoff_projection"
    )
    assert phase2_control_consumer_projection["projection_scope"] == "read_only"
    assert phase2_control_consumer_projection["runtime_authority_blocked"] is True
    assert phase2_control_consumer_projection["runtime_execution_blocked"] is True

    assert set(phase2_control_projection["surface_bindings"]) == set(
        phase1_projection_contract["surface_read_paths"].keys()
    )
    assert (
        set(phase2_control_projection["surface_bindings"])
        == set(phase2_control_consumer_projection["surface_bindings"])
    )

    for surface in phase2_control_projection["surface_bindings"]:
        c1_surface = phase1_consumer_projection["surfaces"][surface]
        c2_surface = phase2_control_projection["surfaces"][surface]
        c3_surface = phase2_control_consumer_projection["surfaces"][surface]

        assert c1_surface["projection_mode"] == "read_only"
        assert c2_surface["projection_mode"] == "read_only"
        assert c3_surface["projection_mode"] == "read_only"

        assert c2_surface["runtime_authority_blocked"] is True
        assert c3_surface["runtime_authority_blocked"] is True

        assert c2_surface["runtime_execution_blocked"] is True
        assert c3_surface["runtime_execution_blocked"] is True

        assert set(c2_surface["contract_refs"]).issubset(
            set(c1_surface["contract_refs"])
        )
        assert set(c2_surface["spine_sources"]).issubset(
            set(phase2_control_projection["projection_bindings"])
        )
        assert set(c3_surface["spine_sources"]).issubset(
            set(phase2_control_projection["projection_bindings"])
        )

"""Phase-0 runtime UI scaffold helpers."""

from .adapter import build_phase0_readonly_projection
from .preview import render_phase0_readonly_projection
from .read_feed import (
    DEFAULT_CONTRACT_PATH,
    DEFAULT_PAYLOAD_PATH,
    ReadFeedContractError,
    ReadFeedGateError,
    ReadFeedPayloadError,
    build_phase1_read_feed_projection,
    build_phase1_read_feed_runtime_projection,
    render_phase1_read_feed_projection,
    run_read_feed_preview,
)
from .runtime_consumer import (
    build_phase1_runtime_ui_consumer_projection,
    run_runtime_consumer_preview,
)
from .phase2_runtime_control import (
    Phase2RuntimeControlError,
    Phase2RuntimeControlShapeError,
    build_phase2_runtime_control_projection,
    run_phase2_runtime_control_preview,
)
from .runtime_control_consumer import (
    Phase2RuntimeControlConsumerError,
    Phase2RuntimeControlConsumerShapeError,
    build_phase2_runtime_control_consumer_projection,
    run_runtime_control_consumer_preview,
)
from .phase_chain import (
    PhaseChainError,
    build_phase0_runtime_ui_scaffold_chain,
    build_phase0_runtime_ui_scaffold_status_snapshot,
    run_phase_chain_preview,
)
from .guardian_suite_seam import (
    EXPECTED_PHASE_GATE_FLAG,
    EXPECTED_PHASE_GATE_NAME,
    DEFAULT_PAYLOAD_PATH as GUARDIAN_SUITE_SEAM_PAYLOAD_PATH,
    GuardianSuiteGateError,
    GuardianSuitePayloadError,
    build_guardian_suite_seam_projection,
    run_guardian_suite_seam_preview,
)

__all__ = [
    "build_phase0_readonly_projection",
    "render_phase0_readonly_projection",
    "DEFAULT_CONTRACT_PATH",
    "DEFAULT_PAYLOAD_PATH",
    "ReadFeedContractError",
    "ReadFeedGateError",
    "ReadFeedPayloadError",
    "build_phase1_read_feed_projection",
    "build_phase1_read_feed_runtime_projection",
    "render_phase1_read_feed_projection",
    "run_read_feed_preview",
    "build_phase1_runtime_ui_consumer_projection",
    "run_runtime_consumer_preview",
    "Phase2RuntimeControlError",
    "Phase2RuntimeControlShapeError",
    "build_phase2_runtime_control_projection",
    "run_phase2_runtime_control_preview",
    "Phase2RuntimeControlConsumerError",
    "Phase2RuntimeControlConsumerShapeError",
    "build_phase2_runtime_control_consumer_projection",
    "run_runtime_control_consumer_preview",
    "PhaseChainError",
    "build_phase0_runtime_ui_scaffold_chain",
    "build_phase0_runtime_ui_scaffold_status_snapshot",
    "run_phase_chain_preview",
    "EXPECTED_PHASE_GATE_NAME",
    "EXPECTED_PHASE_GATE_FLAG",
    "GUARDIAN_SUITE_SEAM_PAYLOAD_PATH",
    "GuardianSuiteGateError",
    "GuardianSuitePayloadError",
    "build_guardian_suite_seam_projection",
    "run_guardian_suite_seam_preview",
]

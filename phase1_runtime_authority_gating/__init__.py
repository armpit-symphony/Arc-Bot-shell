"""Phase-1 runtime authority gating pack helpers.

This module keeps user-intent-to-gate mapping in planning form only. It builds a
deterministic, projection-safe view for later migration and authorization planning.
"""

from .gating import (
    DEFAULT_AUTHORITY_GATING_PACKET_PATH,
    Phase1AuthorityGatingError,
    Phase1AuthorityGatingSchemaError,
    build_phase1_runtime_authority_gating_projection,
    run_phase1_runtime_authority_gating_preview,
)

__all__ = [
    "DEFAULT_AUTHORITY_GATING_PACKET_PATH",
    "Phase1AuthorityGatingError",
    "Phase1AuthorityGatingSchemaError",
    "build_phase1_runtime_authority_gating_projection",
    "run_phase1_runtime_authority_gating_preview",
]

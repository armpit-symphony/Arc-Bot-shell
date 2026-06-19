"""Phase-1 client configuration read-only projection helpers.

This module keeps the client configuration contract in planning form only. It
builds deterministic read-only projections from fixture-backed configuration and
enforces phase gating for any CLI rendering.
"""

from .configuration import (
    DEFAULT_CLIENT_CONFIGURATION_PATH,
    ClientConfigurationPhaseGateError,
    ClientConfigurationSchemaError,
    build_phase1_client_configuration_projection,
    run_phase1_client_configuration_preview,
)

__all__ = [
    "DEFAULT_CLIENT_CONFIGURATION_PATH",
    "ClientConfigurationPhaseGateError",
    "ClientConfigurationSchemaError",
    "build_phase1_client_configuration_projection",
    "run_phase1_client_configuration_preview",
]

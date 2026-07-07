"""Compatibility exports for the Arc-to-LIMA governed preflight adapter."""

from .lima_preflight import (
    ARC_LIMA_CONSUMER,
    ARC_LIMA_SOURCE_POLICY,
    ARC_LIMA_SURFACE,
    ArcLimaFailClosedDecision,
    ArcLimaGovernedPreflightError,
    ArcLimaGovernedPreflightResult,
    call_lima_governed_preflight_for_arc_action,
    map_arc_action_category,
    normalize_for_lima,
    record_lima_governed_preflight_projection,
)

__all__ = [
    "ARC_LIMA_CONSUMER",
    "ARC_LIMA_SOURCE_POLICY",
    "ARC_LIMA_SURFACE",
    "ArcLimaFailClosedDecision",
    "ArcLimaGovernedPreflightError",
    "ArcLimaGovernedPreflightResult",
    "call_lima_governed_preflight_for_arc_action",
    "map_arc_action_category",
    "normalize_for_lima",
    "record_lima_governed_preflight_projection",
]

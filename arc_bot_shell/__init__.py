"""Arc Harness Shell v0.1 public package surface."""

from .contracts import (
    ARC_BLOCK_CATEGORIES,
    ARC_GUARDIAN_STATUSES,
    ARC_SAFE_HARNESS_ACTIONS,
    ArcActionRequest,
    ArcActionRequestError,
    EvidenceBundle,
    GuardianDecision,
    HarnessRunResult,
    LimaRuntimeResult,
)
from .evidence import build_evidence_bundle, default_evidence_dir, write_evidence_bundle
from .guardian import (
    FailClosedGuardian,
    GuardianFacade,
    GuardianSuiteAdapter,
    GuardianUnavailableError,
    TestFakeGuardian,
)
from .harness import run_task_packet
from .lima import (
    DisabledLimaRuntimePort,
    FakeLimaRuntimePort,
    LimaRuntimePort,
    LimaRuntimeUnavailableError,
    LocalLimaImportRuntimePort,
    build_runtime_port,
    load_workspace_lock,
)

__all__ = [
    "ARC_BLOCK_CATEGORIES",
    "ARC_GUARDIAN_STATUSES",
    "ARC_SAFE_HARNESS_ACTIONS",
    "ArcActionRequest",
    "ArcActionRequestError",
    "DisabledLimaRuntimePort",
    "EvidenceBundle",
    "FailClosedGuardian",
    "FakeLimaRuntimePort",
    "GuardianDecision",
    "GuardianFacade",
    "GuardianSuiteAdapter",
    "GuardianUnavailableError",
    "HarnessRunResult",
    "LimaRuntimePort",
    "LimaRuntimeResult",
    "LimaRuntimeUnavailableError",
    "LocalLimaImportRuntimePort",
    "TestFakeGuardian",
    "build_evidence_bundle",
    "build_runtime_port",
    "default_evidence_dir",
    "load_workspace_lock",
    "run_task_packet",
    "write_evidence_bundle",
]

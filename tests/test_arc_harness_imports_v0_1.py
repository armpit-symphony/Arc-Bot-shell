"""Import smoke tests for Arc Harness Shell v0.1."""

from __future__ import annotations


def test_arc_harness_import_surface_is_clean() -> None:
    from arc_bot_shell import (
        ArcActionRequest,
        EvidenceBundle,
        FakeLimaRuntimePort,
        GuardianFacade,
        LocalLimaImportRuntimePort,
        run_task_packet,
    )

    assert ArcActionRequest is not None
    assert EvidenceBundle is not None
    assert FakeLimaRuntimePort is not None
    assert GuardianFacade is not None
    assert LocalLimaImportRuntimePort is not None
    assert run_task_packet is not None

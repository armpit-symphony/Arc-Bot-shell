"""Guardian facade for Arc Harness Shell v0.1."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

from arc_bot_shell.contracts import (
    ARC_BLOCK_CATEGORIES,
    ARC_SAFE_HARNESS_ACTIONS,
    ArcActionRequest,
    GuardianDecision,
)


class GuardianUnavailableError(RuntimeError):
    """Raised when a configured Guardian backend is missing or unusable."""


def _first_block_category(request: ArcActionRequest) -> str | None:
    for capability in request.requested_capabilities:
        if capability in ARC_BLOCK_CATEGORIES:
            return capability
    return None


def _evaluate_local_policy(
    request: ArcActionRequest, evaluator: str
) -> GuardianDecision:
    block_category = _first_block_category(request)
    if block_category is not None:
        return GuardianDecision(
            decision_id=f"guardian-decision:{request.action_id}",
            action_id=request.action_id,
            status="blocked",
            evaluator=evaluator,
            reason=f"{block_category} is blocked in Arc Harness Shell v0.1",
            block_category=block_category,  # type: ignore[arg-type]
            metadata={"preview_only": request.preview_only},
        )

    if request.action_name not in ARC_SAFE_HARNESS_ACTIONS:
        return GuardianDecision(
            decision_id=f"guardian-decision:{request.action_id}",
            action_id=request.action_id,
            status="blocked",
            evaluator=evaluator,
            reason="unsupported harness action",
            block_category="office_system_mutation",
            metadata={"requested_action": request.action_name},
        )

    if request.requires_operator_approval or not request.preview_only:
        return GuardianDecision(
            decision_id=f"guardian-decision:{request.action_id}",
            action_id=request.action_id,
            status="requires_operator_approval",
            evaluator=evaluator,
            reason="request remains preview-safe but requires operator approval before execution",
            metadata={"preview_only": request.preview_only},
        )

    return GuardianDecision(
        decision_id=f"guardian-decision:{request.action_id}",
        action_id=request.action_id,
        status="allowed_preview_only",
        evaluator=evaluator,
        reason="request is limited to a local preview-only harness action",
        metadata={"preview_only": request.preview_only},
    )


@dataclass
class GuardianSuiteAdapter:
    """Best-effort Guardian Suite adapter through the public service entrypoint."""

    import_module: Callable[[str], object] = importlib.import_module
    public_entrypoint: str = "app.services.guardian"

    def is_available(self) -> bool:
        try:
            module = self.import_module(self.public_entrypoint)
        except Exception:
            return False
        return hasattr(module, "get_guardian_suite") or hasattr(
            module, "guardian_suite_inventory"
        )

    def evaluate(self, request: ArcActionRequest) -> GuardianDecision:
        try:
            module = self.import_module(self.public_entrypoint)
        except Exception as exc:
            raise GuardianUnavailableError(str(exc)) from exc
        if not hasattr(module, "get_guardian_suite") and not hasattr(
            module, "guardian_suite_inventory"
        ):
            raise GuardianUnavailableError(
                f"Guardian Suite entrypoint {self.public_entrypoint!r} is missing expected public symbols"
            )
        return _evaluate_local_policy(
            request,
            evaluator="guardian_suite_public_entrypoint",
        )


@dataclass
class FailClosedGuardian:
    """Default Guardian fallback for safe preview-only local harness actions."""

    def evaluate(self, request: ArcActionRequest) -> GuardianDecision:
        return _evaluate_local_policy(request, evaluator="fail_closed_guardian")


@dataclass
class StrictUnavailableGuardian:
    """Fail closed without fabricating a Guardian-owned decision identifier."""

    reason: str = "configured Guardian is unavailable or incompatible"

    def evaluate(self, request: ArcActionRequest) -> GuardianDecision:
        return GuardianDecision(
            decision_id="",
            action_id=request.action_id,
            status="blocked",
            evaluator="guardian_core",
            reason=self.reason,
            allowed=False,
            requires_approval=False,
            requested_action=request.action_name,
            metadata={
                "guardian_adapter": "guardian_core",
                "guardian_status": "unavailable",
                "guardian_allowed": False,
                "guardian_requires_approval": False,
            },
        )


@dataclass
class TestFakeGuardian:
    """Test-only Guardian that allows deterministic status overrides."""

    __test__ = False
    status: str = "allowed_preview_only"
    reason: str = "test fake guardian override"
    block_category: str | None = None

    def evaluate(self, request: ArcActionRequest) -> GuardianDecision:
        return GuardianDecision(
            decision_id=f"guardian-decision:{request.action_id}",
            action_id=request.action_id,
            status=self.status,  # type: ignore[arg-type]
            evaluator="test_fake_guardian",
            reason=self.reason,
            block_category=self.block_category,  # type: ignore[arg-type]
            metadata={"test_double": True},
        )


@dataclass
class GuardianFacade:
    """Arc-facing Guardian facade with a fail-closed fallback."""

    primary: object | None = None
    fallback: object | None = None

    def __post_init__(self) -> None:
        if self.primary is None:
            self.primary = GuardianSuiteAdapter()
        if self.fallback is None:
            self.fallback = FailClosedGuardian()

    def evaluate(
        self,
        request: ArcActionRequest,
        *,
        policy_context: Mapping[str, object] | None = None,
    ) -> GuardianDecision:
        assert self.primary is not None
        assert self.fallback is not None
        try:
            if getattr(self.primary, "adapter_name", None) == "guardian_core":
                return self.primary.evaluate(  # type: ignore[union-attr]
                    request,
                    policy_context=policy_context or {},
                )
            return self.primary.evaluate(request)  # type: ignore[union-attr]
        except Exception as exc:
            if getattr(self.primary, "adapter_name", None) != "guardian_core":
                if not isinstance(exc, GuardianUnavailableError):
                    raise
            if isinstance(self.fallback, StrictUnavailableGuardian):
                self.fallback.reason = str(exc)
            return self.fallback.evaluate(request)  # type: ignore[union-attr]


def build_guardian_facade(
    mode: str,
    *,
    guardian_path: Path | None = None,
    ollama_url: str | None = None,
    contract_reference: str | None = None,
) -> GuardianFacade:
    """Build an explicit Guardian mode without real-to-fake allow fallback."""

    if mode == "guardian_core":
        from .guardian_core_adapter import (
            DEFAULT_GUARDIAN_CONTRACT_REFERENCE,
            DEFAULT_OLLAMA_URL,
            GuardianCoreAdapter,
        )

        return GuardianFacade(
            primary=GuardianCoreAdapter(
                guardian_path=guardian_path,
                endpoint=ollama_url or DEFAULT_OLLAMA_URL,
                contract_reference=(
                    contract_reference or DEFAULT_GUARDIAN_CONTRACT_REFERENCE
                ),
            ),
            fallback=StrictUnavailableGuardian(),
        )
    if mode == "test_fake":
        return GuardianFacade(primary=TestFakeGuardian(), fallback=FailClosedGuardian())
    if mode == "fail_closed":
        return GuardianFacade()
    raise ValueError(f"unsupported Guardian mode: {mode}")

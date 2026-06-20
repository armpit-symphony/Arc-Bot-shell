"""Basic Guardian-gated Arc Bot console projection.

The console surface is intentionally local and preview-only. It describes the
buttons, status lights, upload area, training panel, and chat box without
opening sockets, reading uploaded files, invoking a model, or connecting to
LIMA Office.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HTML_PATH = REPO_ROOT / "ui" / "arc_bot_basic_console.html"
EXPECTED_PHASE_GATE_NAME = "ARC_BOT_BASIC_GUARDIAN_CONSOLE"
EXPECTED_TOOL_PACKS = ("office_docs", "local_model_preview", "spine_readiness")


class BasicConsoleProjectionError(RuntimeError):
    """Raised when the basic console projection would violate shell boundaries."""


def _connection_state(name: str, connected: bool, action_id: str) -> dict[str, Any]:
    return {
        "name": name,
        "status": "connected" if connected else "disconnected",
        "indicator": "green_check" if connected else "red_attention",
        "connect_button_visible": not connected,
        "connect_action": {
            "action_id": action_id,
            "label": f"Connect {name}",
            "guardian_required": True,
            "runtime_execution_blocked": True,
            "network_egress_blocked": True,
            "approval_status": "required_before_execution",
        },
    }


def _assert_guardrails(projection: dict[str, Any]) -> None:
    if projection["runtime_authority_blocked"] is not True:
        raise BasicConsoleProjectionError("Runtime authority must stay blocked")
    if projection["runtime_execution_blocked"] is not True:
        raise BasicConsoleProjectionError("Runtime execution must stay blocked")

    for connection in projection["connections"].values():
        action = connection["connect_action"]
        if action["guardian_required"] is not True:
            raise BasicConsoleProjectionError("Connection actions must require Guardian")
        if action["runtime_execution_blocked"] is not True:
            raise BasicConsoleProjectionError("Connection actions must remain blocked")

    guarded_surfaces = (
        projection["file_upload"],
        projection["training"],
        projection["chat"],
        projection["self_learning"],
    )
    for surface in guarded_surfaces:
        if surface["guardian_required"] is not True:
            raise BasicConsoleProjectionError("Console surfaces must require Guardian")
        if surface["runtime_execution_blocked"] is not True:
            raise BasicConsoleProjectionError("Console surfaces must remain blocked")


def build_basic_guardian_console_projection(
    *,
    local_model_connected: bool = False,
    lima_office_connected: bool = False,
    self_learning_enabled: bool = False,
    phase_gate_name: str = EXPECTED_PHASE_GATE_NAME,
) -> dict[str, Any]:
    """Build the basic Arc Bot console projection for the static UI."""

    if phase_gate_name != EXPECTED_PHASE_GATE_NAME:
        raise BasicConsoleProjectionError(
            f"Unexpected phase gate: {phase_gate_name} != {EXPECTED_PHASE_GATE_NAME}"
        )

    projection: dict[str, Any] = {
        "artifact_id": "arc_bot_basic_guardian_console_v1",
        "artifact_type": "arc_bot_basic_guardian_console_projection",
        "phase": "phase-1",
        "projection_scope": "planning_read_only",
        "source_access_mode": "local_static_projection",
        "guardian_suite_boundary": "sparkbot_guardian_suite",
        "phase_gate": {
            "name": phase_gate_name,
            "required": True,
            "enabled": True,
        },
        "runtime_authority_blocked": True,
        "runtime_execution_blocked": True,
        "local_model_only": True,
        "cloud_fallback_allowed": False,
        "allowed_tool_packs": list(EXPECTED_TOOL_PACKS),
        "connections": {
            "local_model": _connection_state(
                "Local Model",
                local_model_connected,
                "connect-local-model",
            ),
            "lima_office": _connection_state(
                "LIMA Office",
                lima_office_connected,
                "connect-lima-office",
            ),
        },
        "file_upload": {
            "surface": "file_upload",
            "label": "Office document intake",
            "accepted_modes": ["pdf", "image", "docx", "txt"],
            "guardian_required": True,
            "runtime_execution_blocked": True,
            "raw_file_persistence_allowed": False,
            "allowed_result": "redacted_metadata_preview",
        },
        "training": {
            "surface": "training",
            "label": "Training notes",
            "guardian_required": True,
            "runtime_execution_blocked": True,
            "writes_memory_directly": False,
            "allowed_result": "training_draft_pending_review",
        },
        "chat": {
            "surface": "chat",
            "label": "Guardian chat",
            "guardian_required": True,
            "runtime_execution_blocked": True,
            "model_invocation_allowed": False,
            "allowed_result": "queued_preview_request",
        },
        "self_learning": {
            "surface": "self_learning",
            "enabled": self_learning_enabled,
            "mode": "operator_reviewed_memory_candidates",
            "guardian_required": True,
            "runtime_execution_blocked": True,
            "automatic_memory_write_allowed": False,
            "cross_tenant_learning_allowed": False,
        },
    }
    _assert_guardrails(projection)
    return projection


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render the basic Guardian-gated Arc Bot console projection."
    )
    parser.add_argument("--local-model-connected", action="store_true")
    parser.add_argument("--lima-office-connected", action="store_true")
    parser.add_argument("--self-learning-enabled", action="store_true")
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--snapshot-path")
    parser.add_argument(
        "--html-path",
        default=str(DEFAULT_HTML_PATH),
        help="Static console HTML path for operator preview.",
    )
    return parser


def run_basic_console_preview(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        projection = build_basic_guardian_console_projection(
            local_model_connected=args.local_model_connected,
            lima_office_connected=args.lima_office_connected,
            self_learning_enabled=args.self_learning_enabled,
        )
    except BasicConsoleProjectionError as err:
        print(f"basic console preview failed: {err}", file=sys.stderr)
        return 1

    projection["static_html_path"] = str(Path(args.html_path))

    if args.snapshot_path:
        Path(args.snapshot_path).write_text(
            json.dumps(
                projection,
                sort_keys=True,
                indent=None if args.compact else 2,
            )
            + "\n",
            encoding="utf-8",
        )

    json.dump(projection, sys.stdout, indent=None if args.compact else 2, sort_keys=True)
    if not args.compact:
        sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_basic_console_preview()


if __name__ == "__main__":
    raise SystemExit(main())

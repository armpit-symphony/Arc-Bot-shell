"""CLI preview for Arc intent envelope projections."""

from __future__ import annotations

import argparse
import json
import sys

from .base import ArcActionRequest
from .intent_envelope import build_arc_intent_envelope_projection


def run_arc_intent_envelope_preview(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render an Arc intent envelope projection.")
    parser.add_argument("--action-id", default="arc-action-local-doc-preview-001")
    parser.add_argument(
        "--action-kind",
        default="document_intake_preview",
        choices=[
            "document_intake_preview",
            "document_extract_preview",
            "document_draft_generation",
            "document_export_request",
            "connector_request",
            "local_model_call",
            "connector_action",
            "customer_record_mutation",
            "external_send",
            "runtime_tool_execution",
            "admin_remediation",
        ],
    )
    parser.add_argument(
        "--requested-tool-pack",
        default="office_docs",
        choices=["office_docs", "local_model_preview", "spine_readiness"],
    )
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args(argv)

    projection = build_arc_intent_envelope_projection(
        ArcActionRequest(
            action_id=args.action_id,
            action_kind=args.action_kind,
            requested_tool_pack=args.requested_tool_pack,
        )
    )
    json.dump(
        projection,
        sys.stdout,
        sort_keys=True,
        indent=None if args.compact else 2,
    )
    sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_arc_intent_envelope_preview()


if __name__ == "__main__":
    raise SystemExit(main())

"""CLI preview for the Arc Guardian/Spine base projection."""

from __future__ import annotations

import argparse
import json
import sys

from .base import ArcActionRequest, build_arc_guardian_spine_base


def run_arc_guardian_spine_preview(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render the Arc Guardian/Spine base projection."
    )
    parser.add_argument(
        "--action-kind",
        default="document_intake_preview",
        choices=[
            "document_intake_preview",
            "document_extract_preview",
            "local_model_call",
            "connector_action",
            "customer_record_mutation",
            "external_send",
            "runtime_tool_execution",
        ],
    )
    parser.add_argument(
        "--action-id",
        default="arc-action-local-doc-preview-001",
    )
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args(argv)

    projection = build_arc_guardian_spine_base(
        ArcActionRequest(action_id=args.action_id, action_kind=args.action_kind)
    )
    json.dump(
        projection,
        sys.stdout,
        sort_keys=True,
        indent=None if args.compact else 2,
    )
    if not args.compact:
        sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_arc_guardian_spine_preview()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

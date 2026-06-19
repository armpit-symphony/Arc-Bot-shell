"""Read-only seam reader for fixture-backed `app.services.guardian.suite` sources."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping


EXPECTED_PHASE_GATE_NAME = "RUNTIME_UI_SCAFFOLD_PHASE1_FEED"
EXPECTED_PHASE_GATE_FLAG = "runtime_ui_scaffold_guardian_suite_readonly"
EXPECTED_PHASE = "phase-1"
EXPECTED_SOURCE_REFERENCE = "app.services.guardian.suite"
EXPECTED_SOURCE_ACCESS_MODE = "read_only"
EXPECTED_PROJECTION_SCOPE = "read_only"
EXPECTED_SPINE_SOURCES = (
    "guardian_spine_tasks",
    "guardian_spine_events",
    "guardian_spine_approvals",
    "guardian_spine_projects",
)
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAYLOAD_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "arc_bot_guardian_suite_spine_payload.json"
)

ALLOWED_SURFACES = frozenset({"work_queue", "runtime_settings", "overview"})
SOURCE_RECORD_ID_FIELDS = {
    "guardian_spine_tasks": "task_id",
    "guardian_spine_events": "event_id",
    "guardian_spine_approvals": "approval_id",
    "guardian_spine_projects": "project_id",
}


class GuardianSuitePayloadError(ValueError):
    """Raised when guardian suite spine payload does not match read-only contract."""


class GuardianSuiteGateError(RuntimeError):
    """Raised when the guardian suite phase gate is blocked."""


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GuardianSuitePayloadError(f"Expected JSON object at {path}")
    return payload


def _assert_true(value: object, message: str) -> None:
    if value is not True:
        raise GuardianSuitePayloadError(message)


def _assert_list_of_str(
    value: object,
    field_name: str,
    expected: tuple[str, ...] | None = None,
) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise GuardianSuitePayloadError(f"{field_name} must be a list of strings")
    values = list(value)
    if not values:
        raise GuardianSuitePayloadError(f"{field_name} must not be empty")
    if expected is not None and set(values) != set(expected):
        raise GuardianSuitePayloadError(
            f"{field_name} must match exactly {list(expected)}; found {values}"
        )
    return values


def _assert_mapping_record(record: object, source_name: str) -> Mapping[str, Any]:
    if not isinstance(record, Mapping):
        raise GuardianSuitePayloadError(
            f"Each {source_name} item must be an object record"
        )
    if "surface" not in record:
        raise GuardianSuitePayloadError(f"Each {source_name} item must include `surface`")
    if str(record["surface"]) not in ALLOWED_SURFACES:
        raise GuardianSuitePayloadError(f"Unexpected surface in {source_name}: {record['surface']}")
    required_id_field = SOURCE_RECORD_ID_FIELDS[source_name]
    if required_id_field not in record:
        raise GuardianSuitePayloadError(
            f"Each {source_name} item must include `{required_id_field}`"
        )
    if "updated_at" not in record:
        raise GuardianSuitePayloadError(
            f"Each {source_name} item must include `updated_at`"
        )
    return record


def build_guardian_suite_seam_projection(
    *,
    payload_path: str | Path,
    enable_phase_gate: bool = True,
    expected_gate_name: str = EXPECTED_PHASE_GATE_NAME,
) -> dict[str, Any]:
    """Build a validated read-only spine projection from a Guardian Suite payload."""

    payload = _load_json(Path(payload_path))

    if not enable_phase_gate:
        raise GuardianSuiteGateError("Guardian Suite seam preview requires enable_phase_gate=True")

    gate_name = payload.get("phase_gate_name", EXPECTED_PHASE_GATE_NAME)
    if gate_name != expected_gate_name:
        raise GuardianSuiteGateError(
            f"Phase gate mismatch: {gate_name} != {expected_gate_name}"
        )
    gate_required = payload.get("phase_gate_required", False)
    _assert_true(gate_required is True, "Guardian Suite seam projection requires phase gate")

    if payload.get("phase") != EXPECTED_PHASE:
        raise GuardianSuitePayloadError(f"Guardian Suite payload must target {EXPECTED_PHASE}")
    if payload.get("projection_scope") != EXPECTED_PROJECTION_SCOPE:
        raise GuardianSuitePayloadError(
            "Guardian Suite payload must be read_only projection scope"
        )
    if payload.get("source_reference") != EXPECTED_SOURCE_REFERENCE:
        raise GuardianSuitePayloadError(
            f"source_reference must be {EXPECTED_SOURCE_REFERENCE}"
        )
    if payload.get("source_access_mode") != EXPECTED_SOURCE_ACCESS_MODE:
        raise GuardianSuitePayloadError(
            f"source_access_mode must be {EXPECTED_SOURCE_ACCESS_MODE}"
        )

    _assert_true(payload.get("runtime_authority_enabled") is False, "runtime_authority_enabled")

    spine_sources = _assert_list_of_str(
        payload.get("spine_sources"),
        "spine_sources",
        EXPECTED_SPINE_SOURCES,
    )

    spine_records = payload.get("spine_source_records")
    if not isinstance(spine_records, Mapping):
        raise GuardianSuitePayloadError("spine_source_records must be an object")

    normalized_records: dict[str, list[dict[str, Any]]] = {}
    surfaces = set[str]()

    for source in spine_sources:
        records = spine_records.get(source)
        if not isinstance(records, list):
            raise GuardianSuitePayloadError(
                f"spine_source_records[{source}] must be a list"
            )
        normalized = []
        for record in records:
            checked_record = _assert_mapping_record(record, source)
            surface = str(checked_record["surface"])
            surfaces.add(surface)
            normalized.append(dict(checked_record))
        normalized_records[source] = normalized

    return {
        "payload_id": payload.get("payload_id"),
        "payload_type": payload.get("payload_type", "guardian_suite_seam_payload"),
        "artifact_type": "guardian_suite_spine_projection",
        "artifact_id": payload.get("artifact_id", "arc_bot_guardian_suite_spine_projection_v1"),
        "api_status": payload.get("api_status", "CANDIDATE_ONLY"),
        "phase": payload.get("phase"),
        "projection_scope": payload.get("projection_scope"),
        "source_reference": payload["source_reference"],
        "source_access_mode": payload["source_access_mode"],
        "runtime_authority_enabled": False,
        "runtime_authority_required_for_execution": bool(
            payload.get("runtime_authority_required_for_execution", True)
        ),
        "phase_gate": {
            "name": gate_name,
            "required": gate_required,
            "enabled": True,
            "flag": payload.get("phase_gate_flag", EXPECTED_PHASE_GATE_FLAG),
        },
        "ingested_at": payload.get("ingested_at"),
        "spine_sources": spine_sources,
        "spine_record_counts": {
            source: len(records) for source, records in normalized_records.items()
        },
        "surfaces": sorted(surfaces),
        "spine_source_records": normalized_records,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a read-only Guardian Suite seam projection from fixture payload."
    )
    parser.add_argument(
        "payload_path",
        nargs="?",
        default=str(DEFAULT_PAYLOAD_PATH),
        help=(
            "Path to a guardian suite spine payload fixture "
            "(defaults to tests/fixtures/arc_bot_guardian_suite_spine_payload.json)"
        ),
    )
    parser.add_argument(
        "--phase-gate-name",
        default=EXPECTED_PHASE_GATE_NAME,
        help="Expected phase gate name for this projection.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON.",
    )
    parser.add_argument(
        "--snapshot-path",
        help="Write rendered projection JSON to this file.",
    )
    return parser


def run_guardian_suite_seam_preview(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        projection = build_guardian_suite_seam_projection(
            payload_path=Path(args.payload_path),
            expected_gate_name=args.phase_gate_name,
            enable_phase_gate=True,
        )
    except (
        GuardianSuiteGateError,
        GuardianSuitePayloadError,
        OSError,
        ValueError,
    ) as err:
        print(f"guardian suite seam preview failed: {err}", file=sys.stderr)
        return 1
    if args.snapshot_path:
        Path(args.snapshot_path).write_text(
            json.dumps(
                projection,
                sort_keys=True,
                indent=2 if not args.compact else None,
            )
            + "\n",
            encoding="utf-8",
        )

    json.dump(projection, sys.stdout, indent=None if args.compact else 2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def main() -> int:
    return run_guardian_suite_seam_preview()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

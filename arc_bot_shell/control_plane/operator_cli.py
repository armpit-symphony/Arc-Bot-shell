"""Operator CLI for the authenticated Supervisor preflight path.

The preflight itself executes nothing. A granted read-only capability is
performed only when the operator passes Arc's own execution opt-in.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import json
from pathlib import Path
import sys
from typing import Any, TextIO

from .execution import (
    ArcExecutionDenied,
    ArcGrantExecutor,
    expected_capability_for,
)
from .operator_client import (
    ArcSupervisorPreflightClient,
    OperatorResponseReplayStore,
    SupervisorOperatorChannel,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Submit one authenticated Arc operator preflight request. "
            "The command cannot execute the requested action."
        )
    )
    parser.add_argument("--supervisor-url", required=True)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--customer-context-id", required=True)
    parser.add_argument("--operator-id", required=True)
    parser.add_argument("--operator-key-id", required=True)
    parser.add_argument("--worker-id", required=True)
    parser.add_argument(
        "--action",
        required=True,
        choices=(
            "safe_read",
            "status",
            "external_write",
            "shell",
            "credential_access",
            "file_mutation",
            "unknown",
        ),
    )
    parser.add_argument("--resource-type", required=True)
    parser.add_argument("--resource-id", required=True)
    parser.add_argument("--request-id")
    parser.add_argument("--idempotency-key")
    parser.add_argument("--replay-db", type=Path, required=True)
    parser.add_argument(
        "--policy-version",
        default="guardian-policy-lab-v1",
    )
    parser.add_argument(
        "--operator-key-stdin",
        action="store_true",
        required=True,
        help="Read one hex-encoded ephemeral operator key from stdin.",
    )
    parser.add_argument(
        "--execute-granted-capability",
        action="store_true",
        help=(
            "Arc's own execution opt-in. Off unless passed. Even with a valid "
            "Supervisor grant, Arc performs no side effect without this."
        ),
    )
    parser.add_argument(
        "--document-root",
        type=Path,
        default=None,
        help=(
            "Directory a granted document_read may read from. There is no "
            "default, so without it no document can be read."
        ),
    )
    return parser


def _read_operator_key(stream: TextIO) -> bytes:
    encoded = stream.readline().strip()
    if not encoded:
        raise SystemExit("operator key was not provided on stdin")
    try:
        key = bytes.fromhex(encoded)
    except ValueError as exc:
        raise SystemExit("operator key on stdin is not valid hexadecimal") from exc
    finally:
        encoded = ""
    if len(key) < 32:
        raise SystemExit("operator key must contain at least 32 bytes")
    return key


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    operator_key = _read_operator_key(sys.stdin)
    replay_store = OperatorResponseReplayStore(args.replay_db)
    try:
        channel = SupervisorOperatorChannel(
            tenant_id=args.tenant_id,
            customer_context_id=args.customer_context_id,
            actor_id=args.operator_id,
            key_id=args.operator_key_id,
            shared_key=operator_key,
            replay_store=replay_store,
            policy_version=args.policy_version,
        )
        client = ArcSupervisorPreflightClient(
            base_url=args.supervisor_url,
            channel=channel,
        )
        result = client.submit(
            action=args.action,
            resource_type=args.resource_type,
            resource_id=args.resource_id,
            worker_id=args.worker_id,
            request_id=args.request_id,
            idempotency_key=args.idempotency_key,
        )
        output = dict(result)
        output["execution"] = _honour_grant(args, result)
        print(json.dumps(output, indent=2, sort_keys=True))
    finally:
        replay_store.close()
    return 0


def _honour_grant(args: Any, result: Mapping[str, Any]) -> dict[str, Any]:
    """Act on a grant if Arc was opted in, and report why not otherwise.

    A refusal is reported rather than raised so the preflight result is still
    printed. Nothing here runs unless the operator passed Arc's own opt-in.
    """

    executor = ArcGrantExecutor(
        execution_opt_in=args.execute_granted_capability,
        document_root=args.document_root,
    )
    try:
        performed = executor.honour(
            result.get("execution_grant"),
            request_id=str(result.get("request_id") or ""),
            tenant_id=args.tenant_id,
            worker_id=args.worker_id,
            action_type=args.action,
            # Derived from the action Arc asked for, never read back off the
            # grant, so a grant naming a different capability is rejected.
            capability=expected_capability_for(args.action) or "",
            resource_id=args.resource_id,
        )
    except ArcExecutionDenied as denial:
        return {
            "performed": False,
            "reason_code": denial.reason_code,
            "side_effects_performed": False,
        }
    return {
        "performed": True,
        "reason_code": None,
        "capability": performed["capability"],
        "resource_id": performed["resource_id"],
        "byte_count": performed["byte_count"],
        "grant_id": performed["grant_id"],
        "side_effects_performed": performed["side_effects_performed"],
    }


if __name__ == "__main__":
    raise SystemExit(main())

"""Operator CLI for the authenticated non-executing Supervisor preflight path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import TextIO

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
        print(json.dumps(result, indent=2, sort_keys=True))
    finally:
        replay_store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

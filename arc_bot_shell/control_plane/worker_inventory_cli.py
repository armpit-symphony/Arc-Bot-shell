"""Explicit Arc command for the governed non-executing worker inventory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .operator_cli import _read_operator_key
from .operator_client import (
    ArcSupervisorPreflightClient,
    OperatorResponseReplayStore,
    SupervisorOperatorChannel,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Explicitly refresh and display the Supervisor-owned Arc worker "
            "inventory. Every status observation remains non-executing."
        )
    )
    parser.add_argument("--refresh", action="store_true", required=True)
    parser.add_argument("--supervisor-url", required=True)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--customer-context-id", required=True)
    parser.add_argument("--operator-id", required=True)
    parser.add_argument("--operator-key-id", required=True)
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
        result = client.refresh_workers(
            request_id=args.request_id,
            idempotency_key=args.idempotency_key,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
    finally:
        replay_store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

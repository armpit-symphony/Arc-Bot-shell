"""Foreground launcher for the non-executing Arc worker control-plane endpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import TextIO

from .channel import ArcChannelReplayStore, ArcWorkerChannel
from .worker_preview import ArcWorkerPreviewService, build_worker_preview_server


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run one explicit foreground Arc worker metadata endpoint. "
            "This command never executes assignments."
        )
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--customer-context-id", required=True)
    parser.add_argument("--worker-id", required=True)
    parser.add_argument("--worker-role", required=True)
    parser.add_argument("--worker-version", required=True)
    parser.add_argument("--boot-id", required=True)
    parser.add_argument("--key-id", required=True)
    parser.add_argument("--policy-version", default="policy-phase0-v1")
    parser.add_argument("--capability", action="append", required=True)
    parser.add_argument("--replay-db", type=Path, required=True)
    parser.add_argument(
        "--channel-key-stdin",
        action="store_true",
        required=True,
        help=(
            "Read one hex-encoded ephemeral lab channel key from stdin. "
            "The key is not persisted or printed."
        ),
    )
    return parser


def _read_channel_key(stream: TextIO) -> bytes:
    encoded = stream.readline().strip()
    if not encoded:
        raise SystemExit("channel key was not provided on stdin")
    try:
        key = bytes.fromhex(encoded)
    except ValueError as exc:
        raise SystemExit("channel key on stdin is not valid hexadecimal") from exc
    finally:
        encoded = ""
    if len(key) < 32:
        raise SystemExit("channel key must contain at least 32 bytes")
    return key


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    shared_key = _read_channel_key(sys.stdin)
    replay_store = ArcChannelReplayStore(args.replay_db)
    try:
        channel = ArcWorkerChannel(
            tenant_id=args.tenant_id,
            customer_context_id=args.customer_context_id,
            worker_id=args.worker_id,
            key_id=args.key_id,
            shared_key=shared_key,
            replay_store=replay_store,
            policy_version=args.policy_version,
        )
        service = ArcWorkerPreviewService(
            channel=channel,
            worker_role=args.worker_role,
            capabilities=tuple(args.capability),
            worker_version=args.worker_version,
            boot_id=args.boot_id,
        )
        server = build_worker_preview_server(
            host=args.host,
            port=args.port,
            service=service,
        )
        try:
            print(
                json.dumps(
                    {
                        "status": "ready",
                        "host": args.host,
                        "port": server.server_port,
                        "tenant_id": args.tenant_id,
                        "worker_id": args.worker_id,
                        "key_id": args.key_id,
                        "foreground": True,
                        "runtime_authority_blocked": True,
                        "executable": False,
                        "execution_allowed": False,
                        "side_effects_allowed": False,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            server.serve_forever(poll_interval=0.25)
        except KeyboardInterrupt:
            return 0
        finally:
            server.server_close()
    finally:
        replay_store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

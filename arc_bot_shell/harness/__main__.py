"""CLI entrypoint for Arc Harness Shell."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .service import render_run_result, run_task_packet


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Arc Harness Shell release-candidate CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run one task packet through the harness")
    run_parser.add_argument("task_path", type=Path, help="Path to a task packet JSON file")
    run_parser.add_argument(
        "--runtime",
        default="disabled",
        choices=("fake", "local_import", "disabled"),
        help="Runtime adapter to use for non-model-preview actions",
    )
    run_parser.add_argument(
        "--model-adapter",
        default=None,
        choices=("deterministic", "ollama"),
        help="Local model preview adapter for arc.local_model_preview actions",
    )
    run_parser.add_argument(
        "--model",
        default=None,
        help="Optional local model name override for model preview adapters",
    )
    run_parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=None,
        help="Directory for evidence bundle output",
    )
    run_parser.add_argument(
        "--state-path",
        type=Path,
        default=None,
        help="Optional path to a JSONL state store",
    )
    run_parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON output",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command != "run":
        parser.error(f"unsupported command {args.command!r}")
    result = run_task_packet(
        args.task_path,
        runtime_name=args.runtime,
        model_adapter_name=args.model_adapter,
        model_name=args.model,
        evidence_dir=args.evidence_dir,
        state_path=args.state_path,
    )
    print(render_run_result(result, compact=args.compact))
    return result.exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))

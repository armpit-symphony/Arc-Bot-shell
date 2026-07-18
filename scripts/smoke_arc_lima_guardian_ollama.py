"""Explicit real-PC smoke for Arc -> Guardian -> LIMA -> localhost Ollama."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import uuid

from arc_bot_shell.harness import run_task_packet
from arc_bot_shell.integrations import probe_ollama_reachability
from arc_bot_shell.lima import (
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OLLAMA_URL,
    LIMA_ENTRYPOINT,
    LIMA_PINNED_COMMIT,
    LIMA_PINNED_REFERENCE,
    LIMA_PINNED_TAG_OBJECT,
    normalize_loopback_ollama_url,
    resolve_ollama_model,
)
from arc_bot_shell.state import JsonlStateStore


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def _state_for_run(state_path: Path, run_id: str) -> object:
    record = JsonlStateStore(state_path).get_run(run_id)
    _assert(record is not None, f"state record missing for {run_id}")
    return record


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    endpoint = normalize_loopback_ollama_url(
        os.environ.get("ARC_OLLAMA_URL", DEFAULT_OLLAMA_URL)
    )
    model = resolve_ollama_model(
        os.environ.get("ARC_OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    )
    _assert(
        endpoint == "http://127.0.0.1:11434",
        "v0.10 completion smoke requires http://127.0.0.1:11434",
    )
    _assert(model == "qwen2.5:7b", "v0.10 completion smoke requires qwen2.5:7b")

    probe = probe_ollama_reachability(endpoint, model, 2.0)
    _assert(probe.reachable, "Ollama is not reachable on the approved endpoint")
    _assert(probe.model_available, f"configured model {model!r} is not installed")

    guardian_path = Path(
        os.environ.get(
            "ARC_GUARDIAN_PATH",
            str(repo_root.parent / "LIMA-Guardian-Suite"),
        )
    ).resolve()
    _assert(
        (guardian_path / "guardian_core" / "__init__.py").is_file(),
        f"public guardian_core package not found at {guardian_path}",
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    smoke_id = f"{timestamp}-{uuid.uuid4().hex[:8]}"
    smoke_root = repo_root / "artifacts" / "v0_10_ollama_smoke" / smoke_id
    evidence_dir = smoke_root / "evidence"
    state_path = smoke_root / "state" / "runs.jsonl"

    preview = run_task_packet(
        repo_root / "samples" / "tasks" / "local_model_preview.json",
        runtime_name="lima",
        executor_name="ollama",
        model_name=model,
        ollama_url=endpoint,
        evidence_dir=evidence_dir,
        state_path=state_path,
        repo_root=repo_root,
        guardian_mode="guardian_core",
        guardian_path=guardian_path,
    )
    preview_evidence = json.loads(
        preview.evidence_path.read_text(encoding="utf-8")
    )
    preview_state = _state_for_run(state_path, preview.run_id)
    decision_id = preview.guardian_decision_id

    _assert(preview.exit_code == 0, f"local preview failed: {preview.blocked_reason}")
    _assert(preview.guardian_called is True, "Guardian was not called")
    _assert(preview.guardian_status == "allow", "Guardian did not allow preview")
    _assert(bool(decision_id), "Guardian decision_id is missing")
    _assert(preview.eligible_for_lima is True, "request was not LIMA-eligible")
    _assert(preview.lima_called is True, "LIMA was not called")
    _assert(preview.lima_entrypoint == LIMA_ENTRYPOINT, "wrong LIMA entrypoint")
    _assert(
        preview.executor_kind == "loopback_ollama",
        "wrong LIMA executor_kind",
    )
    _assert(preview.executor_call_count == 1, "executor call count was not one")
    _assert(preview.executor_called is True, "executor was not called")
    _assert(preview.ollama_called is True, "Ollama was not called")
    _assert(preview.endpoint == endpoint, "Ollama endpoint changed")
    _assert(preview.model == model, "Ollama model changed")
    _assert(preview.network_called is True, "network call was not reported")
    _assert(preview.network_scope == "loopback_only", "network scope changed")
    _assert(preview.credentials_used is False, "credentials were used")
    _assert(preview.external_side_effects is False, "side effects were reported")
    _assert(bool(preview.output_text.strip()), "Ollama response text is empty")
    _assert(preview.evidence_written is True, "preview evidence was not written")
    _assert(preview.state_written is True, "preview state was not written")
    _assert(
        preview.lima_input_guardian_decision_id == decision_id,
        "decision_id changed in LIMA input",
    )
    _assert(
        preview.executor_input_guardian_decision_id == decision_id,
        "decision_id changed in executor input",
    )
    _assert(
        preview.runtime_output.get("guardian_decision_id") == decision_id,
        "decision_id changed in LIMA result",
    )
    _assert(
        preview_evidence.get("guardian_decision_id") == decision_id,
        "decision_id changed in evidence",
    )
    _assert(
        getattr(preview_state, "guardian_decision_id", None) == decision_id,
        "decision_id changed in state",
    )
    _assert(
        "output_text" not in preview_evidence.get("runtime_metadata", {}),
        "full Ollama output was persisted in runtime evidence metadata",
    )

    blocked = run_task_packet(
        repo_root / "samples" / "tasks" / "external_email_send.json",
        runtime_name="lima",
        executor_name="ollama",
        model_name=model,
        ollama_url=endpoint,
        evidence_dir=evidence_dir,
        state_path=state_path,
        repo_root=repo_root,
        guardian_mode="guardian_core",
        guardian_path=guardian_path,
    )
    blocked_evidence = json.loads(
        blocked.evidence_path.read_text(encoding="utf-8")
    )
    blocked_state = _state_for_run(state_path, blocked.run_id)
    _assert(
        blocked.guardian_status in {"deny", "requires_approval"},
        "external email was not denied or approval-gated",
    )
    _assert(blocked.lima_called is False, "denied external email reached LIMA")
    _assert(blocked.executor_called is False, "denied external email reached executor")
    _assert(blocked.ollama_called is False, "denied external email reached Ollama")
    _assert(blocked.network_called is False, "denied external email used network")
    _assert(blocked.execution_allowed is False, "external execution was enabled")
    _assert(blocked.evidence_written is True, "blocked evidence was not written")
    _assert(blocked.state_written is True, "blocked state was not written")
    _assert(blocked_evidence.get("lima_called") is False, "blocked evidence is false")
    _assert(
        getattr(blocked_state, "execution_allowed", None) is False,
        "blocked state enabled execution",
    )

    summary = {
        "status": "ok",
        "arc_flow": "Arc -> Guardian -> LIMA -> loopback Ollama",
        "guardian_called": preview.guardian_called,
        "guardian_status": preview.guardian_status,
        "guardian_decision_id": decision_id,
        "same_decision_id_in_lima_input_result_evidence_state": True,
        "lima_called": preview.lima_called,
        "lima_entrypoint": preview.lima_entrypoint,
        "lima_pinned_reference": LIMA_PINNED_REFERENCE,
        "lima_pinned_commit": LIMA_PINNED_COMMIT,
        "lima_pinned_tag_object": LIMA_PINNED_TAG_OBJECT,
        "executor_kind": preview.executor_kind,
        "executor_call_count": preview.executor_call_count,
        "ollama_called": preview.ollama_called,
        "endpoint": preview.endpoint,
        "model": preview.model,
        "network_called": preview.network_called,
        "network_scope": preview.network_scope,
        "credentials_used": preview.credentials_used,
        "external_side_effects": preview.external_side_effects,
        "duration_ms": preview.duration_ms,
        "output_text_nonempty": bool(preview.output_text.strip()),
        "output_character_count": len(preview.output_text),
        "output_preview": " ".join(preview.output_text.split())[:160],
        "evidence_written": preview.evidence_written,
        "evidence_path": str(preview.evidence_path),
        "state_written": preview.state_written,
        "state_path": str(state_path),
        "external_email": {
            "guardian_status": blocked.guardian_status,
            "lima_called": blocked.lima_called,
            "executor_called": blocked.executor_called,
            "ollama_called": blocked.ollama_called,
            "network_called": blocked.network_called,
            "execution_allowed": blocked.execution_allowed,
            "evidence_written": blocked.evidence_written,
            "state_written": blocked.state_written,
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

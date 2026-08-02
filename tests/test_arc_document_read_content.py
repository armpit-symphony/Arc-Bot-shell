"""Returning document content is a separate, explicitly requested step.

Reading a document and showing it are different acts. The read is what the
grant authorizes; showing the text is what the operator asks for on top. These
tests hold the line between them, and hold the rule that content never travels
inside the machine-readable result.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any

import pytest

from arc_bot_shell.control_plane import operator_cli
from arc_bot_shell.control_plane.execution import ArcGrantExecutor


NOW = datetime.now(timezone.utc).replace(microsecond=0)
BODY = "Q3 revenue summary.\nSecond line.\n"


def _grant(**overrides: Any) -> dict[str, Any]:
    grant = {
        "grant_contract": "lima.governed_execution_grant",
        "grant_version": "v0.1",
        "grant_mode": "single_use_operator_gated",
        "grant_id": "grant:content001",
        "decision_id": "decision:content001",
        "request_id": "request-content-001",
        "guardian_decision_id": "gd-content-001",
        "policy_version": "guardian-policy-lab-v1",
        "policy_snapshot_hash": "sha256:" + "a" * 64,
        "guardian_binding_hash": "sha256:" + "b" * 64,
        "granted_capability": "document_read",
        "bound_tenant_id": "tenant-lab-001",
        "bound_worker_id": "arc-worker-001",
        "bound_action_type": "safe_read",
        "scope_hash": "sha256:" + "c" * 64,
        "nonce": "nonce-content-001",
        "issued_at": NOW.isoformat().replace("+00:00", "Z"),
        "expires_at": (NOW + timedelta(seconds=120)).isoformat().replace("+00:00", "Z"),
        "execution_allowed": True,
        "side_effects_allowed": False,
        "requires_operator_opt_in": True,
    }
    grant.update(overrides)
    return grant


class _Args:
    def __init__(self, **kwargs: Any) -> None:
        self.tenant_id = "tenant-lab-001"
        self.worker_id = "arc-worker-001"
        self.action = "safe_read"
        self.resource_id = "report.txt"
        self.execute_granted_capability = True
        self.document_root: Path | None = None
        self.emit_document_content = False
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.fixture
def document_root(tmp_path: Path) -> Path:
    # Written as bytes: write_text would translate newlines on Windows and the
    # fixture would no longer be the bytes these assertions describe.
    (tmp_path / "report.txt").write_bytes(BODY.encode("utf-8"))
    return tmp_path


_UNSET = object()


def _result(grant: Any = _UNSET) -> dict[str, Any]:
    return {
        "request_id": "request-content-001",
        "execution_grant": _grant() if grant is _UNSET else grant,
    }


# --- the flag ---------------------------------------------------------------


def test_flag_defaults_off() -> None:
    parser = operator_cli._parser()
    args = parser.parse_args(
        [
            "--supervisor-url", "http://127.0.0.1:8080",
            "--tenant-id", "t", "--customer-context-id", "c",
            "--operator-id", "o", "--operator-key-id", "k",
            "--worker-id", "w", "--action", "safe_read",
            "--resource-type", "worker_status", "--resource-id", "r",
            "--replay-db", "replay.db", "--operator-key-stdin",
        ]
    )
    assert args.emit_document_content is False


def test_read_happens_but_content_is_withheld_by_default(
    document_root: Path,
) -> None:
    args = _Args(document_root=document_root)
    record, content = operator_cli._honour_grant_with_content(args, _result())

    assert record["performed"] is True
    assert record["byte_count"] == len(BODY.encode("utf-8"))
    assert content is None
    assert record["content_emitted"] is False
    assert record["content_reason_code"] == "content_not_requested"


def test_content_is_returned_when_explicitly_requested(
    document_root: Path,
) -> None:
    args = _Args(document_root=document_root, emit_document_content=True)
    record, content = operator_cli._honour_grant_with_content(args, _result())

    assert record["performed"] is True
    assert content == BODY
    assert record["content_emitted"] is True
    assert record["content_reason_code"] is None


# --- content never rides inside the result ----------------------------------


def test_result_record_never_carries_content_even_when_emitted(
    document_root: Path,
) -> None:
    """A logged or piped result must not leak the document."""

    args = _Args(document_root=document_root, emit_document_content=True)
    record, content = operator_cli._honour_grant_with_content(args, _result())

    assert content == BODY
    assert "content" not in record
    rendered = json.dumps(record)
    assert "Q3 revenue summary" not in rendered
    assert "Second line" not in rendered


def test_legacy_honour_grant_still_returns_a_content_free_record(
    document_root: Path,
) -> None:
    args = _Args(document_root=document_root, emit_document_content=True)
    record = operator_cli._honour_grant(args, _result())

    assert "content" not in record
    assert "Q3 revenue summary" not in json.dumps(record)


# --- content requires the same gates as the read ----------------------------


def test_content_cannot_be_obtained_without_arcs_execution_opt_in(
    document_root: Path,
) -> None:
    """The content flag must not be a way around the execution opt-in."""

    args = _Args(
        document_root=document_root,
        emit_document_content=True,
        execute_granted_capability=False,
    )
    record, content = operator_cli._honour_grant_with_content(args, _result())

    assert content is None
    assert record["performed"] is False
    assert record["reason_code"] == "arc_execution_opt_in_disabled"
    assert record["content_emitted"] is False


def test_content_cannot_be_obtained_without_a_grant(document_root: Path) -> None:
    args = _Args(document_root=document_root, emit_document_content=True)
    record, content = operator_cli._honour_grant_with_content(args, _result(None))

    assert content is None
    assert record["reason_code"] == "execution_grant_absent"


def test_content_cannot_be_obtained_for_a_mismatched_grant(
    document_root: Path,
) -> None:
    args = _Args(document_root=document_root, emit_document_content=True)
    mismatched = _grant(granted_capability="draft_workspace")
    record, content = operator_cli._honour_grant_with_content(
        args, _result(mismatched)
    )

    assert content is None
    assert record["reason_code"] == "execution_grant_binding_mismatch"


def test_emitting_content_is_not_a_side_effect(document_root: Path) -> None:
    args = _Args(document_root=document_root, emit_document_content=True)
    record, _ = operator_cli._honour_grant_with_content(args, _result())

    assert record["side_effects_performed"] is False


# --- non-text documents -----------------------------------------------------


def test_binary_document_is_counted_but_not_shown(tmp_path: Path) -> None:
    """Lossy decoding would show plausible text that is not the file."""

    (tmp_path / "report.txt").write_bytes(b"\xff\xfe\x00binary\x00payload")
    args = _Args(document_root=tmp_path, emit_document_content=True)
    record, content = operator_cli._honour_grant_with_content(args, _result())

    assert record["performed"] is True
    assert record["byte_count"] == 17
    assert content is None
    assert record["content_emitted"] is False
    assert record["content_reason_code"] == "document_not_utf8_text"


def test_executor_reports_whether_the_document_decoded(tmp_path: Path) -> None:
    (tmp_path / "text.txt").write_bytes(b"plain")
    (tmp_path / "blob.bin").write_bytes(b"\xff\xfe\x00")
    executor = ArcGrantExecutor(execution_opt_in=True, document_root=tmp_path)

    text = executor.honour(
        _grant(), request_id="request-content-001", tenant_id="tenant-lab-001",
        worker_id="arc-worker-001", action_type="safe_read",
        capability="document_read", resource_id="text.txt",
    )
    blob = executor.honour(
        _grant(), request_id="request-content-001", tenant_id="tenant-lab-001",
        worker_id="arc-worker-001", action_type="safe_read",
        capability="document_read", resource_id="blob.bin",
    )

    assert text["is_utf8_text"] is True
    assert text["content"] == "plain"
    assert blob["is_utf8_text"] is False
    assert blob["content"] is None
    assert blob["byte_count"] == 3


def test_utf8_document_with_non_ascii_is_returned_intact(tmp_path: Path) -> None:
    body = "Café résumé — naïve\n"
    (tmp_path / "report.txt").write_bytes(body.encode("utf-8"))
    args = _Args(document_root=tmp_path, emit_document_content=True)
    record, content = operator_cli._honour_grant_with_content(args, _result())

    assert content == body
    assert record["byte_count"] == len(body.encode("utf-8"))


# --- how it is printed ------------------------------------------------------


def test_content_is_printed_in_a_delimited_block(
    capsys: pytest.CaptureFixture[str],
) -> None:
    record = {"resource_id": "report.txt", "byte_count": len(BODY)}
    operator_cli._emit_content(record, BODY)
    out = capsys.readouterr().out

    assert "--- BEGIN DOCUMENT CONTENT" in out
    assert "--- END DOCUMENT CONTENT ---" in out
    assert BODY in out
    assert out.index("BEGIN") < out.index("Q3 revenue") < out.index("END")


def test_content_without_a_trailing_newline_still_closes_cleanly(
    capsys: pytest.CaptureFixture[str],
) -> None:
    operator_cli._emit_content({"resource_id": "r", "byte_count": 5}, "abcde")
    lines = capsys.readouterr().out.splitlines()

    assert lines[-2] == "abcde"
    assert lines[-1] == "--- END DOCUMENT CONTENT ---"


# --- end to end through main() ----------------------------------------------


def _main_argv(replay_db: Path, document_root: Path, emit: bool) -> list[str]:
    argv = [
        "--supervisor-url", "http://127.0.0.1:8080",
        "--tenant-id", "tenant-lab-001",
        "--customer-context-id", "customer-context-main",
        "--operator-id", "operator-lab-001", "--operator-key-id", "operator-key-001",
        "--worker-id", "arc-worker-001",
        "--action", "safe_read",
        "--resource-type", "document", "--resource-id", "report.txt",
        "--replay-db", str(replay_db),
        "--operator-key-stdin",
        "--execute-granted-capability",
        "--document-root", str(document_root),
    ]
    if emit:
        argv.append("--emit-document-content")
    return argv


class _StubClient:
    def __init__(self, **_: Any) -> None:
        pass

    def submit(self, **_: Any) -> dict[str, Any]:
        return _result()


@pytest.fixture
def stubbed_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    """Drive main() without a Supervisor, keeping the real grant handling."""

    import io

    monkeypatch.setattr(operator_cli, "ArcSupervisorPreflightClient", _StubClient)
    monkeypatch.setattr(
        operator_cli, "SupervisorOperatorChannel", lambda **_: object()
    )
    monkeypatch.setattr(
        operator_cli,
        "OperatorResponseReplayStore",
        lambda *_a, **_k: type("_S", (), {"close": lambda self: None})(),
    )
    monkeypatch.setattr("sys.stdin", io.StringIO("00" * 32 + "\n"))


def test_main_prints_content_block_when_requested(
    stubbed_cli: None,
    document_root: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = operator_cli.main(_main_argv(tmp_path / "r.db", document_root, emit=True))
    out = capsys.readouterr().out
    payload, _, block = out.partition("--- BEGIN DOCUMENT CONTENT")

    assert code == 0
    # The JSON half must parse and must not contain the document.
    parsed = json.loads(payload)
    assert parsed["execution"]["content_emitted"] is True
    assert "Q3 revenue summary" not in payload
    # The content half must carry it.
    assert "Q3 revenue summary." in block
    assert "--- END DOCUMENT CONTENT ---" in block


def test_main_stays_pure_json_when_content_is_not_requested(
    stubbed_cli: None,
    document_root: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = operator_cli.main(_main_argv(tmp_path / "r.db", document_root, emit=False))
    out = capsys.readouterr().out

    assert code == 0
    parsed = json.loads(out)
    assert parsed["execution"]["performed"] is True
    assert parsed["execution"]["content_emitted"] is False
    assert "BEGIN DOCUMENT CONTENT" not in out
    assert "Q3 revenue summary" not in out

"""Foreground Arc worker launcher tests."""

from __future__ import annotations

from io import StringIO

import pytest

from arc_bot_shell.control_plane.cli import _parser, _read_channel_key


def test_channel_key_is_read_only_from_stdin() -> None:
    key = _read_channel_key(StringIO("11" * 32 + "\n"))
    assert key == bytes.fromhex("11" * 32)


@pytest.mark.parametrize("value", ["", "not-hex", "11" * 31])
def test_missing_invalid_or_short_channel_key_fails_closed(value: str) -> None:
    with pytest.raises(SystemExit):
        _read_channel_key(StringIO(value + "\n"))


def test_launcher_requires_explicit_identity_capability_replay_store_and_stdin_key() -> None:
    parser = _parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])

    args = parser.parse_args(
        [
            "--tenant-id",
            "tenant-lab-001",
            "--customer-context-id",
            "customer-context-main",
            "--worker-id",
            "arc-worker-001",
            "--worker-role",
            "general_office_arc_worker",
            "--worker-version",
            "arc-bot-shell-0.1.0",
            "--boot-id",
            "boot-lab-001",
            "--key-id",
            "ephemeral-key-001",
            "--capability",
            "document_read",
            "--replay-db",
            "arc-replay.db",
            "--channel-key-stdin",
        ]
    )

    assert args.host == "127.0.0.1"
    assert args.port == 0
    assert args.channel_key_stdin is True
    assert args.capability == ["document_read"]

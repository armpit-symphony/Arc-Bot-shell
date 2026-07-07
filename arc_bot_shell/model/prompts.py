"""Prompt helpers for local Arc model previews."""

from __future__ import annotations

from typing import Any

from arc_bot_shell.contracts import ArcActionRequest, GuardianDecision


def _task_packet(payload: dict[str, Any]) -> dict[str, Any]:
    task_packet = payload.get("task_packet")
    if isinstance(task_packet, dict):
        return task_packet
    return {}


def build_prompt_summary(request: ArcActionRequest) -> str:
    task_packet = _task_packet(request.payload)
    payload_keys = sorted(request.payload.keys())
    title = task_packet.get("title") or request.payload.get("title") or request.summary
    return (
        f"Draft a local operator preview for {request.task_ref}. "
        f"Requested action: {request.action_name}. "
        f"Summary: {request.summary} "
        f"Primary topic: {title}. "
        f"Payload keys: {', '.join(payload_keys) if payload_keys else 'none'}."
    )


def build_deterministic_draft(
    request: ArcActionRequest,
    decision: GuardianDecision,
    prompt_summary: str,
) -> str:
    task_packet = _task_packet(request.payload)
    subject = task_packet.get("title") or request.payload.get("topic") or "the task packet"
    notes = task_packet.get("notes") or request.payload.get("payload_summary") or request.summary
    source = task_packet.get("source") or request.payload.get("source") or "local task packet"
    return (
        f"Operator preview for {subject}: {notes} "
        f"Source: {source}. Guardian status: {decision.status}. "
        f"No external action was taken and no customer-facing message was sent. "
        f"This draft was generated from a local preview-only task packet. "
        f"Prompt summary: {prompt_summary}"
    )

# LIMA Office Team Phase 2 Ollama/Qwen Readiness Handoff

Status: request sent, LIMA Office response received, Arc Bot read-only mapping
implemented.

## Original Message

Please review the Arc Bot Phase 2 local model readiness contract and confirm the
LIMA Office fields needed for worker attachment and model-route status.

Arc Bot is adding an Ollama/Qwen local model readiness projection only. It does
not call Ollama, invoke a model, open sockets, read secrets, or mutate LIMA
Office. The current target local model family is Qwen through Ollama, with the
default planning model tag `qwen2.5:7b` and localhost endpoint label
`http://127.0.0.1:11434`.

What Arc Bot needs from LIMA Office:

- Worker identity fields:
  - `worker_id`
  - `tenant_id`
  - worker display name
  - supervisor/server attachment status
- Model-route/readiness fields:
  - approved runtime family: `ollama`
  - approved model family: `qwen`
  - approved model tag or model alias
  - localhost endpoint label or route ID
  - model-route status values: ready, setup_required, blocked, degraded
- Local seat health fields:
  - Ollama installed attestation
  - Ollama service reachable attestation
  - Qwen model present attestation
  - hardware profile: CPU threads, RAM GB, GPU label, VRAM GB, free storage GB
- Guardian/evidence fields:
  - Guardian decision ref for any future model invocation
  - evidence refs for install/model/worker attachment checks
  - policy refs for local-model-only, no-cloud-fallback, and no-provider-token posture
- Boundaries to confirm:
  - no cloud fallback
  - no provider credentials
  - no cross-tenant learning
  - no model call until Guardian approval path exists
  - no connector/customer-system mutation from Arc Bot readiness checks

Please send back the canonical LIMA Office schema or event names for these
fields so Arc Bot can map its Phase 2 projection into LIMA Office without
inventing a second source of truth.

## Confirmed Arc Mapping

Arc Bot consumes the LIMA Office handoff as read-only packet metadata through
`build_ollama_qwen_readiness_from_lima_packet`.

Confirmed safe packet fields:

- `worker_id`
- `tenant_id`
- `supervisor_attachment_status = operator_attested_no_probe`
- `route_mode` limited to `mock_only` or `local_planned`
- `route_status` limited to `selected`, `degraded`, `denied`, `blocked_mvp`,
  or `unavailable`
- `approved_runtime_family = ollama`
- `approved_model_family = qwen`
- `approved_model_alias`
- `localhost_endpoint_label_or_route_id`
- `hardware_profile_ref`
- `attestation_refs`
- `guardian_decision_refs`
- `evidence_refs`
- grouped `policy_refs`
- `blocked_capabilities`

Arc Bot status mapping:

- `route_status = selected` and `route_mode = local_planned` may display as
  ready when required refs are present.
- `route_status = degraded` displays as setup-required.
- `route_status = denied`, `blocked_mvp`, or `unavailable` displays as blocked.
- `route_mode = mock_only` displays as setup-required, never live-ready.

The packet does not authorize Ollama calls, Qwen inference, endpoint probing,
provider tokens, live connectors, external sends, remediation, or runtime
execution.

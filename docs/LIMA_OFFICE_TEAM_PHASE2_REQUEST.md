# Message To LIMA Office Team - Phase 2 Ollama/Qwen Readiness

Please review the Arc Bot Phase 2 local model readiness contract and confirm
the LIMA Office fields needed for worker attachment and model-route status.

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

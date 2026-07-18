# Arc v0.10 Guardian, LIMA, and Loopback Ollama

Arc v0.10 proves the first real local model vertical integration:

`ArcActionRequest -> real Guardian allow -> installed LIMA v1.1 -> Arc-supplied loopback_ollama executor -> localhost Ollama -> evidence/state/history`

The milestone is local model preview only. It does not authorize external
email, file mutation, browser, connector, device, robotics, office-system, LAN,
public-network, credential, or cloud-provider execution.

## Pinned contracts

- Guardian tag: `guardian-core-v1.1-local-model-preview-policy`
- Guardian commit: `69e843218c521b913edcec404dea6b7be8c64f06`
- LIMA tag: `lima-runtime-v1.1-loopback-ollama-executor`
- LIMA merge commit: `deea1c4f5b6d3455a7e97e4b621e22b8d22a6244`
- LIMA annotated tag object: `23470f3341fe6f70ebf3595efb9aef07791beed8`
- Public import: `from lima.harness import execute_v1_live_provider_model_call`

The package dependency uses the tagged Git reference. Clean-clone CI does not
require a sibling LIMA checkout or an Ollama installation.

## Trust path

Arc accepts only a real Guardian `allowed_preview_only` result whose public
Guardian metadata reports `allow`, `allowed=true`, `requires_approval=false`,
and a non-empty Guardian-generated `decision_id`. The requested action must be
exactly `arc.local_model_preview` and remain preview-only.

Arc then submits `executor_kind=loopback_ollama` to LIMA with:

- `network_scope=loopback_only`;
- `credentials_used=false`;
- `external_side_effects=false`;
- an HTTP `127.0.0.1` or `localhost` base URL with an explicit port;
- one configured non-empty model name.

LIMA validates this request before invoking Arc's callable. Arc counts the
executor invocation and fails closed unless it occurs exactly once. The
executor independently revalidates Guardian lineage, executor kind, action,
endpoint, credentials, and side-effect flags before network use.

## HTTP boundary

The executor calls only `POST /api/generate` with streaming disabled and a
bounded local-preview prompt. Redirects are not followed. Remote, LAN,
wildcard, IPv6, credentialed, HTTPS, path-bearing, query-bearing,
fragment-bearing, whitespace-padded, missing-port, and malformed URLs fail
before network.

Expected failures are normalized as `service_unavailable`,
`model_unavailable`, `timeout`, `malformed_response`, or `executor_error`.
Failures after an HTTP attempt truthfully retain `network_called=true` and
`ollama_called=true`. There is no model or provider fallback.

## Evidence and state

The exact Guardian `decision_id` is checked in the LIMA request, executor
input, LIMA result, evidence, and state. Evidence records executor, endpoint,
model, loopback scope, duration, status, and sanitized error metadata. It does
not persist the full generated output; it stores a length/hash/reference.
The CLI result may return the generated local preview to the operator.

## Explicit local smoke

```powershell
$env:ARC_GUARDIAN_PATH = "C:\Users\limap\LIMA-Guardian-Suite"
$env:ARC_OLLAMA_URL = "http://127.0.0.1:11434"
$env:ARC_OLLAMA_MODEL = "qwen2.5:7b"
python scripts/smoke_arc_lima_guardian_ollama.py
```

The script verifies model availability but never installs or pulls a model. It
runs the approved preview and then proves that external email remains blocked
before LIMA, the executor, Ollama, or network.

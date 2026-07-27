# Arc Operator Preflight

`arc-preflight` is the first real Arc operator path into the LIMA Office
control plane. It sends one authenticated structured request to an explicit
foreground Supervisor and displays the signed governed result.

```text
Arc operator
→ arc-preflight
→ authenticated Supervisor
→ mandatory Guardian
→ LIMA governed decision
→ SQLite evidence
→ Arc worker assignment preview
→ Arc acknowledgement
→ operator-visible result
→ stop
```

The request includes a bounded action, resource, worker, request ID, and
idempotency key. It does not include actor role or action category; the
Supervisor binds the configured operator identity and derives classification
server-side.

The ephemeral operator HMAC key is read only from stdin. The key is never
accepted as a command-line argument or environment variable and is not stored
in the response replay database.

The first lab endpoint is loopback-only. Private-LAN transport remains blocked
until confidentiality and durable operator/device key provisioning are
reviewed.

Every response must preserve:

- `runtime_authority_blocked=true`
- `executable=false`
- `execution_allowed=false`
- `side_effects_allowed=false`

The client rejects responses with an unexpected contract shape, identity,
policy, signature, payload hash, expiry, nonce replay, static LIMA fallback, or
any execution-authorizing flag.

This path performs no model/provider/Ollama call, tool or connector execution,
external send, credential access, file mutation, approval execution, hidden
background work, robotics, IoT, drone, or physical-world action.

## Explicit worker inventory refresh

`arc-workers --refresh` is the Arc operator's worker observation surface. The
explicit foreground command asks the Supervisor to refresh its server-owned
registry. Arc cannot provide worker identities, roles, classifications,
eligibility, or authority in this request.

For each of the Supervisor's 1-8 registered workers, the Supervisor derives a
status preflight and requires Guardian, LIMA, durable evidence, and a
non-executing Arc acknowledgement. The signed result shows health, eligibility,
last heartbeat time, policy decision identities, and evidence references.
Offline or quarantined workers remain visible but ineligible. A missing or
invalid Guardian/LIMA decision fails the whole inventory closed without
exposing ungoverned worker details.

The refresh uses the same stdin-only operator key and loopback-only lab
transport as `arc-preflight`. It has no background polling and performs no
worker action beyond the non-executing heartbeat and assignment-preview path.

## Explicit durable evidence read

`arc-evidence --read --target-request-id <request-id>` displays one persisted,
redacted control-plane trace through the same authenticated operator channel.
Arc supplies the target request reference only. It cannot choose the Arc
worker, classification, actor role, capability, eligibility, or authority.

The Supervisor derives a safe-read evidence operation, selects an
authenticated Arc worker, and requires mandatory Guardian, Guardian-backed
LIMA, and a non-executing Arc acknowledgement before reading the trace.
Available events must belong to the channel-bound tenant and operator. Missing
and other-actor records both return `not_found`; neither leaks target events.
The client validates the exact response and event allowlists, identity
bindings, payload hashes, reason codes, and all blocked execution flags.

The trace survives a Supervisor restart because it is read from the
Supervisor's SQLite evidence spine. The evidence query creates its own durable
authorization chain and `evidence_read` record. Query replay, missing
Guardian/LIMA authority, unavailable workers, invalid signatures, and
evidence-writer failure all fail closed. The command does not execute the
recorded action or perform provider, model, tool, connector, network, file,
credential, approval, background, or physical-world work.

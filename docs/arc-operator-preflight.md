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

# Arc Worker Control-Plane Boundary

Arc now exposes a library-built, explicit foreground HTTP endpoint for the
first LIMA Office lab control-plane proof.

Supported metadata-only operations:

- authenticated registration response;
- authenticated heartbeat response;
- non-executing assignment-preview acknowledgement or rejection.

The endpoint does not start itself or create a hidden background service. A
caller must explicitly build it with `build_worker_preview_server(...)` and run
the returned single-threaded server.

Every channel message binds:

- tenant and worker identity;
- opaque key ID;
- message type;
- payload SHA-256;
- short issue/expiry window;
- replay nonce and message ID;
- HMAC-SHA256 signature.

The injected lab channel key must contain at least 32 bytes. It is never
persisted by Arc; the SQLite replay store records only message identity,
payload hash metadata, expiry, and the opaque key ID.

The first server builder accepts loopback addresses only. The matching LIMA
Office smoke command is documented in that repository’s
`docs/runbooks/arc-worker-control-plane-smoke.md`.

All registration and assignment responses preserve:

```text
runtime_authority_blocked=true
executable=false
execution_allowed=false
side_effects_allowed=false
```

No model, provider, Ollama, tool, connector, external send, customer
credential, file mutation, approval execution, scheduler, robotics, IoT,
drone, or physical-world path is present in this endpoint.

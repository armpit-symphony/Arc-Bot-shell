# Arc v0.10 Ollama Route — Retired

This document records a historical Arc → LIMA → loopback Ollama experiment.
That route is not an active or supported Arc control-plane API.

The following surfaces are permanently quarantined:

- the retired `lima.harness` execution API;
- Arc's direct loopback Ollama executor;
- the direct Ollama reachability/model probe;
- `scripts/smoke_arc_lima_guardian_ollama.py`.

Each retained compatibility entry point fails closed before model, provider,
tool, connector, credential, filesystem, or network activity. Arc does not
provide a compatibility shim for the retired execution API.

The supported milestone is the non-executing flow:

```text
Supervisor → mandatory Guardian decision → lima.runtime.run_governed_request
→ Arc assignment preview/acknowledgement → durable evidence → stop
```

All governed results preserve:

```text
executable=false
execution_allowed=false
side_effects_allowed=false
```

Provider, model, Ollama, tool, connector, external-send, credential,
background, robotics, IoT, drone, and physical-world execution remain out of
scope.

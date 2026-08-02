# Running the lab

How to bring up a real Supervisor and a real Arc worker and drive one governed
request through them. Everything here is loopback-only and foreground.

## What you need

- Python 3.11
- A checkout of [Lima-Office](https://github.com/armpit-symphony/Lima-Office)
- The governed stack installed in Office's environment:
  `python -m pip install -r requirements-lab.txt`

Office installs LIMA and Guardian Suite at the commits its `stack.lock.json`
declares. Arc installs its own, deliberately different, LIMA pin. They are
separate environments; do not try to make one satisfy both.

## The fastest path: let the smokes do it

Office ships scripts that stand up both processes, run a scenario, and tear
everything down. Run these from the Office checkout:

```bash
# Worker registration, heartbeat, non-executing assignment
python scripts/arc-worker-control-plane-smoke.py --arc-source /path/to/Arc-Bot-shell

# Operator -> Supervisor -> Guardian -> LIMA -> back, no execution
python scripts/arc-operator-supervisor-smoke.py --arc-source /path/to/Arc-Bot-shell

# The grant path, and every gate denying
python scripts/arc-execution-grant-smoke.py --arc-source /path/to/Arc-Bot-shell

# One, two, and eight workers
python scripts/arc-multi-worker-supervisor-smoke.py --arc-source /path/to/Arc-Bot-shell --worker-count 8
```

The grant smoke is the interesting one. It proves four scenarios, three of
which are refusals:

| Scenario | Result |
|---|---|
| Both opt-ins on | A real document read happens |
| Supervisor opt-in off | No grant issued — `execution_grant_absent` |
| Arc opt-in off | Grant issued, Arc refuses — `arc_execution_opt_in_disabled` |
| No document root | Nothing readable — `document_root_not_configured` |

## Driving it by hand

Three processes, each in its own terminal. Keys are ephemeral, passed only on
stdin, and never persisted or printed.

### 1. Arc worker

```bash
arc-worker-preview \
  --host 127.0.0.1 --port 0 \
  --tenant-id tenant-lab-001 \
  --customer-context-id customer-context-main \
  --worker-id arc-worker-001 \
  --worker-role general_office_arc_worker \
  --worker-version arc-bot-shell-0.1.0 \
  --boot-id boot-lab-001 \
  --key-id worker-key-001 \
  --policy-version guardian-policy-lab-v1 \
  --capability document_read \
  --capability it_diagnostics_read_only \
  --replay-db worker-replay.db \
  --channel-key-stdin
```

Note the flag is `--channel-key-stdin` here; the Supervisor uses
`--worker-key-stdin` for the matching key. Feed the same hex key to both.

`--port 0` binds an ephemeral port. Arc prints a readiness JSON line
containing the port it chose, along with `executable: false`.

### 2. Supervisor

From the Office checkout:

```bash
python -m lima_office.supervisor.cli \
  --host 127.0.0.1 --port 0 \
  --tenant-id tenant-lab-001 \
  --customer-context-id customer-context-main \
  --operator-id operator-lab-001 --operator-key-id operator-key-001 \
  --worker-id arc-worker-001 --worker-key-id worker-key-001 \
  --worker-url http://127.0.0.1:<worker-port> \
  --evidence-db supervisor.db \
  --policy-version guardian-policy-lab-v1 \
  --operator-key-stdin --worker-key-stdin \
  --execution-opt-in
```

`--tenant-id`, `--customer-context-id`, `--worker-id`, `--worker-key-id`, and
`--policy-version` must match the worker exactly or the channel will not
authenticate.

Feed it the hex operator key on the first stdin line and the matching worker
key on the second. Drop `--execution-opt-in` and the Supervisor will never
issue a grant, whatever Arc asks for.

### 3. Operator request

```bash
arc-preflight \
  --supervisor-url http://127.0.0.1:<supervisor-port> \
  --tenant-id tenant-lab-001 --customer-context-id customer-context-main \
  --operator-id operator-lab-001 --operator-key-id operator-key-001 \
  --worker-id arc-worker-001 \
  --action safe_read --resource-type document --resource-id report.txt \
  --policy-version guardian-policy-lab-v1 \
  --replay-db operator-replay.db --operator-key-stdin \
  --execute-granted-capability --document-root /path/to/documents
```

`--resource-id` is resolved relative to `--document-root`, so `report.txt`
means `/path/to/documents/report.txt`.

Drop `--execute-granted-capability` and Arc refuses the grant it was handed.
Drop `--document-root` and it has nothing it is allowed to read.

## Reading the result

The result always carries the governed decision, and always reports
`executable`, `execution_allowed`, and `side_effects_allowed` as `false` — a
decision never authorizes execution, in any scenario.

If a read happened, `execution.performed` is `true` and you get
`byte_count`, `capability`, `resource_id`, and `grant_id`. You never get
document content; that is deliberate.

If it did not, `execution.reason_code` says why.

## When something refuses

Refusals are the normal case, and each has a fixed reason code. Look it up
before assuming a bug:

| Reason code | Meaning |
|---|---|
| `execution_grant_absent` | The Supervisor was not started with `--execution-opt-in` |
| `arc_execution_opt_in_disabled` | Arc was not started with `--execute-granted-capability` |
| `document_root_not_configured` | Arc has no directory it may read from |
| `execution_grant_binding_mismatch` | The grant does not match what Arc asked for |
| `execution_grant_expired` | Grants are capped at a 300-second TTL |
| `document_outside_root` | Path containment rejected the resource |

## Things that will bite you

- **Loopback is enforced on both sides.** The Supervisor refuses to bind a
  non-loopback address and Arc refuses to call one. This is not configurable.
- **Grants are single use.** Replaying one loses a `UNIQUE` constraint race at
  the Supervisor rather than being honoured twice.
- **Arc and Office pin different LIMA commits on purpose.** If you install
  Office's LIMA into Arc's environment, Arc's RC1 attestation test fails. That
  test is doing its job.
- **An install from before 2026-08-01** carries a stale LIMA trust baseline in
  its operator config. It loads and self-corrects on first run, so
  `lima_pinned_commit` changing once between your first and second health check
  is the migration, not a fault.

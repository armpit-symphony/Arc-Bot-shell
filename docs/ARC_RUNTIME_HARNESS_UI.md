# Arc Runtime Harness UI

Status: physical-PC test surface. Not a production operator console.

`ui/arc_runtime_harness.html` is the Arc-owned renderer for the LIMA Office
physical test harness. LIMA Office serves it on loopback and remains the source
of truth for mode, gates, SOP records, outcomes, counters, and evidence.

## Training mode

- Startup default.
- Accepts a task reference, operator role, and reviewed SOP instruction.
- Persists through LIMA Office as an operator-authored SOP record.
- Does not expose the governed-read endpoint through the controller.
- Cannot alter Guardian policy or teach past a forbidden denial.

## Working mode

- Disabled in the UI until LIMA Office reports all startup gates ready.
- Exposes only a task reference and document path relative to the configured
  document root.
- Calls the LIMA Office harness API, which sends the request through the real
  Supervisor, Guardian decision, grant issue, and Arc grant-consumption path.
- Shows the routed outcome, denial disposition, escalation, evidence reference,
  and returned content when content emission was enabled at launch.

## Browser state boundary

The page holds only transient display state. It does not use `localStorage`,
`sessionStorage`, IndexedDB, cookies, or URL state as product authority. Dynamic
text, including document content, is rendered with `textContent`; the page does
not inject response data as HTML.

The page makes same-origin requests only:

- `GET /api/state`
- `POST /api/mode`
- `POST /api/training/instruction`
- `POST /api/work/read`
- `POST /api/worker/status`

The LIMA Office launcher and full test runbook are documented in its
`docs/ARC_RUNTIME_HARNESS.md`.

## Still blocked

This UI is not a general-purpose IDE. It has no task-queue editor, arbitrary
tool runner, terminal, browser automation, connector control, external send,
file mutation, model invocation, remediation, or physical-device control.

The next UI slices should be queue visibility, resumable-task state, paged
document reads, approval review, and customer escalation-ladder configuration.
Each needs its server-side contract and evidence path before a button is added.

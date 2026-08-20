# Arc operator IDE adapter

Status: bounded physical-PC test lane. Not production-ready.

Arc owns the local task queue, approval records, and next-task selection policy.
The `ArcOperatorIDE` adapter projects those existing stores to the LIMA Office
localhost harness. It does not create another queue or execute a task.

The projection contains:

- queue standing and the reason Arc selected the next workable task;
- up to 100 recent task records;
- pending approval metadata, without document or evidence-file contents;
- authority metadata that explicitly keeps approvals non-executable.

A blocked task is ready only when its latest result is
`requires_operator_approval` and one of these explicit signals exists:

- its Arc approval record is `approved`; or
- LIMA Office supplies its task ID or task reference after an SOP gap is
  instructed.

Denied approvals and tasks blocked by a control never become selectable.
Recording an approval updates evidence/state only and keeps
`execution_allowed=false`. Any later document read still enters the real
Supervisor and Guardian path and requires a fresh single-use grant.

The adapter serializes access within the IDE process. The JSONL stores remain a
local test implementation, not a multi-process or multi-worker production
queue.

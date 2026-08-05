# Which task Arc picks up next

A task manager puts jobs in a queue. Arc returns to open tasks that needed more
information before it could finish them, and only when there are none of those
does it start something new.

```
blocked, and the answer has arrived   ->  resume it
otherwise, oldest queued              ->  start it
otherwise                             ->  nothing to do
```

`arc_bot_shell/tasks/selection.py`.

## Why blocked work comes first

A blocked task is work already begun, and usually work somebody has already
been asked about. Starting a fresh job while an answer sits unused wastes the
more expensive thing — a person's attention — and leaves the queue with more
in progress than anyone is finishing.

Age does not override this. An older queued task still waits behind a blocked
task whose answer has arrived, because the answer is the scarce thing.

## "Blocked" means two different things, and only one comes back

`intake.py` maps both results onto the same status:

```python
if result_status in {"blocked", "requires_operator_approval"}:
    return "blocked"
```

- `requires_operator_approval` — waiting on a person. **Resumable.**
- `blocked` — a control refused it. **Never resumable.**

Nothing downstream can tell them apart by status alone, so the selector reads
`latest_result_status` and refuses to resume a refused task **regardless of
`resolved_task_ids`**. Resolution names tasks whose *answer* arrived, and no
answer overturns a refusal.

Without that guard, listing a refused task's id would hand the same request
back after a control declined it — the queue-level form of retrying a
`forbidden` denial, which Lima-Office refuses at the routing level. A control
that can be walked around one layer up is not a control.

`RESUMABLE_BLOCKED_RESULTS` is an allowlist, so an unrecognised result — or
none at all — stays put. The cost of that default is a task needing a person to
close it; the cost of the opposite is a refused request being tried again
because somebody listed its id.

## A blocked task is only offered once its answer has arrived

This is the part that looks like a detail and is not.

`resolved_task_ids` names the blocked tasks whose missing information has since
arrived — an SOP instruction written, an approval decided. A blocked task not
named there is **still waiting and is not offered**.

Offer it anyway and the worker loops: the task blocks for the same reason, is
selected again because it is still the oldest blocked task, and the queue stops
moving while looking busy. That is the same failure as retrying a denial with
nothing changed, one level up.

Resolution is an explicit input rather than something the selector infers, so a
caller cannot hand back a task that is still waiting by accident.

## Ordering is total

Oldest first, with `task_id` breaking ties. A manager queuing a batch will
create several tasks in the same second, and a selector that returned them in
arbitrary order would make a run impossible to reproduce.

## The number worth watching

```python
queue_standing(tasks, resolved_task_ids=[...])
# {"queued": 4, "blocked": 3, "blocked_ready": 1,
#  "blocked_waiting": 1, "blocked_terminal": 1, "workable": 5}
```

`blocked_terminal` is counted apart from `blocked_waiting` because those tasks
will never move. They were refused, and no answer resumes them — they need
closing, not resolving. Folding them together would make a queue look like it
is waiting on people who cannot help it.

`blocked_waiting` is how much of the queue is stalled on **people** rather than
on Arc. It is the honest counterpart to Lima-Office's `autonomy_rate`: as SOP
accumulates and Arc needs asking less often, this should fall.

`workable` is what Arc can pick up right now. When it is zero and
`blocked_waiting` is not, Arc is idle and waiting on somebody — which is worth
seeing, because it looks identical to an idle queue from the outside.

## What this does not do

It selects; it does not run anything. Handing the selected task to the governed
path, and routing whatever comes back, is Lima-Office's
`route_task_outcome` — see `docs/TASK_SEAM.md` there.

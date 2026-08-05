"""Which task Arc picks up next.

The operating model is: a task manager puts jobs in a queue, Arc returns to
open tasks that needed more information before it could finish them, and only
when there are none of those does it start something new.

That order is not arbitrary. A blocked task is work already begun, and usually
work a person has already been asked about. Starting a fresh job while an
answer sits unused wastes the more expensive thing - somebody's attention - and
leaves the queue with more work in progress than anyone is finishing.

A blocked task is only picked up again once the thing it was waiting for has
arrived. Picking one up without that is how a worker loops: the task blocks for
the same reason, is selected again because it is still the oldest blocked task,
and nothing moves. ``resolved_task_ids`` is therefore an explicit input rather
than something inferred here, so a caller cannot accidentally hand back a task
that is still waiting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Collection, Iterable, Sequence

from .models import TaskRecord


# Statuses a selector will ever consider. running tasks belong to whoever is
# running them; completed and failed ones are finished with.
SELECTABLE_STATUSES = ("blocked", "queued")

# Why a task was chosen, recorded so a queue's behaviour can be explained
# after the fact rather than reasoned about from its ordering.
SELECTION_REASONS = (
    "resumed_after_information_arrived",
    "started_from_the_queue",
)


class TaskSelectionError(RuntimeError):
    """The queue or the resolution set is not something to select from."""


@dataclass(frozen=True)
class TaskSelection:
    """The task to work next, and why it was chosen over the others."""

    task: TaskRecord
    reason: str
    blocked_waiting: int = 0
    queued_waiting: int = 0

    def __post_init__(self) -> None:
        if self.reason not in SELECTION_REASONS:
            raise TaskSelectionError(
                f"unknown selection reason {self.reason!r}; expected one of "
                f"{list(SELECTION_REASONS)}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_type": "task_selection",
            "task_id": self.task.task_id,
            "task_ref": self.task.task_ref,
            "status": self.task.status,
            "reason": self.reason,
            "blocked_waiting": self.blocked_waiting,
            "queued_waiting": self.queued_waiting,
        }


def _ordered(records: Iterable[TaskRecord]) -> list[TaskRecord]:
    """Oldest first, with task_id breaking ties so the order is total.

    Two tasks created in the same second are not unusual when a manager queues
    a batch, and a selector that returned them in arbitrary order would make a
    run impossible to reproduce.
    """

    return sorted(records, key=lambda record: (record.created_at, record.task_id))


def select_next_task(
    tasks: Sequence[TaskRecord],
    *,
    resolved_task_ids: Collection[str] = (),
) -> TaskSelection | None:
    """Return the next task to work, or None if nothing is workable.

    ``resolved_task_ids`` names the blocked tasks whose missing information has
    since arrived - an SOP instruction written, an approval decided. A blocked
    task not named there is still waiting and is not offered.
    """

    if isinstance(tasks, (str, bytes)) or not isinstance(tasks, Sequence):
        raise TaskSelectionError("tasks must be a sequence of TaskRecord")
    if isinstance(resolved_task_ids, (str, bytes)):
        raise TaskSelectionError(
            "resolved_task_ids must be a collection of ids, not a single string"
        )
    resolved = {str(task_id) for task_id in resolved_task_ids}

    blocked = [record for record in tasks if record.status == "blocked"]
    queued = [record for record in tasks if record.status == "queued"]
    ready = [record for record in blocked if record.task_id in resolved]

    if ready:
        return TaskSelection(
            task=_ordered(ready)[0],
            reason="resumed_after_information_arrived",
            blocked_waiting=len(blocked) - len(ready),
            queued_waiting=len(queued),
        )
    if queued:
        return TaskSelection(
            task=_ordered(queued)[0],
            reason="started_from_the_queue",
            blocked_waiting=len(blocked),
            queued_waiting=len(queued) - 1,
        )
    return None


def selectable_tasks(tasks: Sequence[TaskRecord]) -> list[TaskRecord]:
    """Everything a selector could ever offer, in the order it would offer it.

    Blocked before queued, oldest first within each. Useful for showing an
    operator what the worker will do next without asking it to do anything.
    """

    blocked = _ordered(record for record in tasks if record.status == "blocked")
    queued = _ordered(record for record in tasks if record.status == "queued")
    return [*blocked, *queued]


def queue_standing(
    tasks: Sequence[TaskRecord],
    *,
    resolved_task_ids: Collection[str] = (),
) -> dict[str, Any]:
    """How much work is waiting, and how much of it is actually workable.

    ``blocked_waiting`` is the number that will not move until somebody
    supplies something. It is the honest measure of how much of the queue is
    stalled on people rather than on Arc, and it is the number that should fall
    as SOP accumulates.
    """

    resolved = {str(task_id) for task_id in resolved_task_ids}
    blocked = [record for record in tasks if record.status == "blocked"]
    ready = [record for record in blocked if record.task_id in resolved]
    counts = {status: 0 for status in SELECTABLE_STATUSES}
    for record in tasks:
        if record.status in counts:
            counts[record.status] += 1
    return {
        "record_type": "task_queue_standing",
        "queued": counts["queued"],
        "blocked": counts["blocked"],
        "blocked_ready": len(ready),
        "blocked_waiting": len(blocked) - len(ready),
        "workable": len(ready) + counts["queued"],
    }

"""Proofs for which task Arc picks up next.

The operating model: Arc returns to open tasks that needed more information,
and only when there are none of those does it start something new.

The case that matters most is the one that looks like a detail - a blocked
task whose information has *not* arrived must not be offered. Offer it and the
worker loops: it blocks for the same reason, is selected again because it is
still the oldest blocked task, and the queue stops moving while looking busy.
"""

from __future__ import annotations

from typing import Any

import unittest

from arc_bot_shell.tasks.models import TaskRecord
from arc_bot_shell.tasks.selection import (
    RESUMABLE_BLOCKED_RESULTS,
    SELECTION_REASONS,
    TaskSelection,
    TaskSelectionError,
    is_resumable,
    queue_standing,
    select_next_task,
    selectable_tasks,
)


# A default that also substitutes for an explicit None would silently rewrite
# the case under test - "no recorded result" is exactly one of the values that
# must not be resumable.
_UNSET = object()


def _task(
    task_id: str,
    status: str,
    created_at: str,
    latest_result_status: Any = _UNSET,
) -> TaskRecord:
    """A task record. Blocked ones default to waiting on a person.

    intake maps both ``requires_operator_approval`` and ``blocked`` onto the
    blocked status, so a fixture that leaves the result unset is not a blocked
    task at all - it is one whose reason for stopping is unknown, which the
    selector treats as terminal.
    """

    if latest_result_status is _UNSET:
        latest_result_status = (
            "requires_operator_approval" if status == "blocked" else None
        )
    return TaskRecord(
        task_id=task_id,
        action_id=f"action-{task_id}",
        task_ref=f"task:{task_id}",
        requested_action="arc.read_document",
        payload_summary="read a document",
        source="task_manager",
        status=status,  # type: ignore[arg-type]
        created_at=created_at,
        updated_at=created_at,
        latest_result_status=latest_result_status,
    )


def _refused(task_id: str, created_at: str) -> TaskRecord:
    """A task a control refused. It must never come back."""

    return _task(task_id, "blocked", created_at, latest_result_status="blocked")


class BlockedBeforeQueuedTests(unittest.TestCase):
    """Finishing started work beats starting new work."""

    def setUp(self) -> None:
        self.blocked = _task("b1", "blocked", "2026-08-01T09:00:00Z")
        self.queued = _task("q1", "queued", "2026-08-01T08:00:00Z")

    def test_a_resolved_blocked_task_wins_over_an_older_queued_one(self):
        """Age does not beat the fact that somebody already answered."""

        selection = select_next_task(
            [self.queued, self.blocked], resolved_task_ids=["b1"]
        )
        self.assertEqual("b1", selection.task.task_id)
        self.assertEqual("resumed_after_information_arrived", selection.reason)

    def test_an_unresolved_blocked_task_is_not_offered(self):
        """The loop this prevents: reselecting a task still waiting."""

        selection = select_next_task([self.queued, self.blocked])
        self.assertEqual("q1", selection.task.task_id)
        self.assertEqual("started_from_the_queue", selection.reason)

    def test_nothing_workable_returns_nothing(self):
        self.assertIsNone(select_next_task([self.blocked]))

    def test_an_empty_queue_returns_nothing(self):
        self.assertIsNone(select_next_task([]))

    def test_running_and_finished_tasks_are_never_offered(self):
        for status in ("running", "completed", "failed"):
            with self.subTest(status=status):
                self.assertIsNone(
                    select_next_task([_task("x", status, "2026-08-01T00:00:00Z")])
                )


class RefusedWorkNeverComesBackTests(unittest.TestCase):
    """The queue-level form of retrying a forbidden denial.

    intake collapses ``requires_operator_approval`` and ``blocked`` onto one
    status, so nothing downstream can tell "waiting for a person" apart from
    "a control refused it" by status alone. Resolution names tasks whose answer
    arrived, and no answer overturns a refusal.
    """

    def test_a_refused_task_is_not_offered_even_when_listed_as_resolved(self):
        selection = select_next_task(
            [_refused("injection", "2026-08-01T00:00:00Z")],
            resolved_task_ids=["injection"],
        )
        self.assertIsNone(selection)

    def test_a_refused_task_loses_to_a_queued_one(self):
        selection = select_next_task(
            [
                _refused("injection", "2026-08-01T00:00:00Z"),
                _task("q1", "queued", "2026-08-02T00:00:00Z"),
            ],
            resolved_task_ids=["injection"],
        )
        self.assertEqual("q1", selection.task.task_id)

    def test_a_waiting_task_beside_a_refused_one_is_still_resumable(self):
        """The guard must not block the case it exists alongside."""

        selection = select_next_task(
            [
                _refused("injection", "2026-08-01T00:00:00Z"),
                _task("waiting", "blocked", "2026-08-02T00:00:00Z"),
            ],
            resolved_task_ids=["injection", "waiting"],
        )
        self.assertEqual("waiting", selection.task.task_id)

    def test_only_named_results_are_resumable(self):
        self.assertTrue(
            is_resumable(
                _task("t", "blocked", "2026-08-01T00:00:00Z", "requires_operator_approval")
            )
        )
        for result in ("blocked", "failed", "something_new", None):
            with self.subTest(result=result):
                self.assertFalse(
                    is_resumable(_task("t", "blocked", "2026-08-01T00:00:00Z", result))
                )

    def test_only_blocked_tasks_are_ever_resumable(self):
        for status in ("queued", "running", "completed", "failed"):
            with self.subTest(status=status):
                self.assertFalse(
                    is_resumable(_task("t", status, "2026-08-01T00:00:00Z"))
                )

    def test_a_refused_task_is_never_listed_as_selectable(self):
        listing = selectable_tasks(
            [
                _refused("injection", "2026-08-01T00:00:00Z"),
                _task("waiting", "blocked", "2026-08-02T00:00:00Z"),
            ]
        )
        self.assertEqual(["waiting"], [record.task_id for record in listing])


class OrderingTests(unittest.TestCase):
    """Oldest first, and reproducibly so."""

    def test_the_oldest_queued_task_goes_first(self):
        selection = select_next_task(
            [
                _task("new", "queued", "2026-08-02T00:00:00Z"),
                _task("old", "queued", "2026-08-01T00:00:00Z"),
            ]
        )
        self.assertEqual("old", selection.task.task_id)

    def test_the_oldest_resolved_blocked_task_goes_first(self):
        selection = select_next_task(
            [
                _task("newer", "blocked", "2026-08-02T00:00:00Z"),
                _task("older", "blocked", "2026-08-01T00:00:00Z"),
            ],
            resolved_task_ids=["newer", "older"],
        )
        self.assertEqual("older", selection.task.task_id)

    def test_tasks_created_in_the_same_moment_have_a_stable_order(self):
        """A manager queuing a batch must not make a run irreproducible."""

        stamp = "2026-08-01T00:00:00Z"
        batch = [_task("c", "queued", stamp), _task("a", "queued", stamp)]
        first = select_next_task(batch).task.task_id
        second = select_next_task(list(reversed(batch))).task.task_id
        self.assertEqual(first, second)
        self.assertEqual("a", first)

    def test_selectable_tasks_lists_blocked_before_queued(self):
        listing = selectable_tasks(
            [
                _task("q", "queued", "2026-08-01T00:00:00Z"),
                _task("b", "blocked", "2026-08-02T00:00:00Z"),
                _task("done", "completed", "2026-08-01T00:00:00Z"),
            ]
        )
        self.assertEqual(["b", "q"], [record.task_id for record in listing])


class SelectionRecordTests(unittest.TestCase):
    """A selection explains itself."""

    def test_a_selection_reports_what_it_passed_over(self):
        selection = select_next_task(
            [
                _task("b1", "blocked", "2026-08-01T00:00:00Z"),
                _task("b2", "blocked", "2026-08-01T00:00:00Z"),
                _task("q1", "queued", "2026-08-01T00:00:00Z"),
                _task("q2", "queued", "2026-08-01T00:00:00Z"),
            ],
            resolved_task_ids=["b1"],
        )
        self.assertEqual(1, selection.blocked_waiting)
        self.assertEqual(2, selection.queued_waiting)

    def test_starting_fresh_work_does_not_count_itself_as_waiting(self):
        selection = select_next_task(
            [
                _task("q1", "queued", "2026-08-01T00:00:00Z"),
                _task("q2", "queued", "2026-08-02T00:00:00Z"),
            ]
        )
        self.assertEqual(1, selection.queued_waiting)

    def test_a_selection_renders_for_evidence(self):
        rendered = select_next_task(
            [_task("q1", "queued", "2026-08-01T00:00:00Z")]
        ).to_dict()
        self.assertEqual("task_selection", rendered["record_type"])
        self.assertEqual("task:q1", rendered["task_ref"])

    def test_an_unknown_reason_is_refused(self):
        with self.assertRaises(TaskSelectionError):
            TaskSelection(
                task=_task("q1", "queued", "2026-08-01T00:00:00Z"),
                reason="felt_like_it",
            )

    def test_every_reason_is_one_a_selection_can_actually_carry(self):
        self.assertEqual(2, len(set(SELECTION_REASONS)))


class InputRefusalTests(unittest.TestCase):
    """A single string is the mistake worth catching."""

    def test_a_bare_string_of_ids_is_refused(self):
        """'b1' would otherwise resolve every task whose id is one character."""

        with self.assertRaises(TaskSelectionError):
            select_next_task(
                [_task("b", "blocked", "2026-08-01T00:00:00Z")],
                resolved_task_ids="b",
            )

    def test_tasks_must_be_a_sequence(self):
        for tasks in ("task", 7, None):
            with self.subTest(tasks=tasks):
                with self.assertRaises(TaskSelectionError):
                    select_next_task(tasks)


class QueueStandingTests(unittest.TestCase):
    """How much of the queue is stalled on people rather than on Arc."""

    def _queue(self):
        return [
            _task("b1", "blocked", "2026-08-01T00:00:00Z"),
            _task("b2", "blocked", "2026-08-01T00:00:00Z"),
            _task("q1", "queued", "2026-08-01T00:00:00Z"),
            _task("done", "completed", "2026-08-01T00:00:00Z"),
        ]

    def test_refused_work_is_counted_apart_from_work_awaiting_an_answer(self):
        """Folding them together makes a queue look like it waits on people
        who cannot help it."""

        standing = queue_standing(
            [*self._queue(), _refused("injection", "2026-08-01T00:00:00Z")]
        )
        self.assertEqual(3, standing["blocked"])
        self.assertEqual(2, standing["blocked_waiting"])
        self.assertEqual(1, standing["blocked_terminal"])

    def test_refused_work_is_never_workable(self):
        standing = queue_standing(
            [_refused("injection", "2026-08-01T00:00:00Z")],
            resolved_task_ids=["injection"],
        )
        self.assertEqual(0, standing["workable"])
        self.assertEqual(0, standing["blocked_ready"])

    def test_blocked_waiting_is_the_number_stalled_on_somebody(self):
        standing = queue_standing(self._queue(), resolved_task_ids=["b1"])
        self.assertEqual(2, standing["blocked"])
        self.assertEqual(1, standing["blocked_ready"])
        self.assertEqual(1, standing["blocked_waiting"])

    def test_workable_counts_only_what_arc_can_pick_up_now(self):
        standing = queue_standing(self._queue(), resolved_task_ids=["b1"])
        self.assertEqual(2, standing["workable"])

    def test_finished_tasks_are_not_counted(self):
        standing = queue_standing(self._queue())
        self.assertEqual(1, standing["queued"])
        self.assertEqual(2, standing["blocked"])

    def test_nothing_resolved_means_nothing_blocked_is_workable(self):
        standing = queue_standing(self._queue())
        self.assertEqual(0, standing["blocked_ready"])
        self.assertEqual(1, standing["workable"])

    def test_standing_agrees_with_what_selection_does(self):
        """The number shown and the task offered must not disagree."""

        queue = self._queue()
        standing = queue_standing(queue)
        selection = select_next_task(queue)
        self.assertEqual(standing["workable"] > 0, selection is not None)


if __name__ == "__main__":
    unittest.main()

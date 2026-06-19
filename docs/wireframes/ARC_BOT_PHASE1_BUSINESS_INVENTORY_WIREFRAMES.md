# Arc Bot Phase-1 Business Inventory Wireframes

Date: 2026-06-19
Status: read-only planning artifact

These wireframes define the first operator-visible inventory surfaces for Arc Bot Phase-1. They are planning artifacts only and do not add frontend routes, persistence, connector access, model calls, worker dispatch, or runtime authority.

## Shared Surface Rules

- Every panel renders from `tests/fixtures/arc_bot_phase1_business_inventory.json`.
- Every panel remains `read_only` or `planning_read_only`.
- Every panel must display blocked runtime actions before any future action affordance.
- Metadata actions are notes, filters, or references only.
- Missing policy, evidence, or runbook metadata must render as `review_required` or `blocked`.

## Primary Operator Layout

```text
+----------------------+----------------------+----------------------+
| Overview             | Work Queue           | Runtime Settings     |
| readiness summary    | task posture         | model/local posture  |
| blocked actions      | no dispatch          | no route mutation    |
+----------------------+----------------------+----------------------+
| Workers              | Tasks                | Approvals            |
| node posture         | task metadata        | review posture       |
| no service control   | no execution         | no self-approval     |
+----------------------+----------------------+----------------------+
| Guardian             | Evidence             | Connectors           |
| decision refs        | evidence refs        | readiness only       |
| no overrides         | no raw secrets       | no OAuth/live I/O    |
+----------------------+----------------------+----------------------+
| Governance / Audit   | Runbooks             | Model / Local AI     |
| review refs          | blocked guidance     | readiness notes      |
| no breakglass        | no diagnostics       | no provider calls    |
+----------------------+----------------------+----------------------+
```

## Surface Inventory

| Surface | First viewport content | Allowed metadata actions | Blocked runtime emphasis |
| --- | --- | --- | --- |
| `overview` | Business role focus, readiness summary, open blockers | `open_runbook`, `open_related_record` | no dispatch, no remediation, no live inference |
| `work_queue` | Queue counts, task posture, assignment intent | `create_local_queue_entry`, `attach_work_docs`, `add_readiness_blocker_note` | no program execution, no customer writes, no external sends |
| `runtime_settings` | Runtime posture, model route notes, setup blockers | `stage_seat_edits`, `record_readiness_metadata` | no route mutation, no token storage, no live inference |
| `workers` | Worker inventory posture and enrollment blockers | `request_enrollment_review`, `request_reenrollment_review`, `link_worker_evidence` | no service start/stop, no quarantine release, no tool-pack broadening |
| `tasks` | Task metadata, risk labels, approval labels | `inspect_task`, `filter_by_status`, `draft_operator_note` | no task run, no external send, no customer record mutation |
| `approvals` | Pending approval posture and evidence requirements | `review_pending_approval`, `record_intended_outcome_note` | no self-approval, no approval token issue, no action execution |
| `guardian` | Guardian decision refs and replay posture | `inspect_decision`, `link_runbook_to_decision` | no override, no prompt trust escalation, no secret reveal |
| `evidence` | Evidence metadata, linked task refs, failure refs | `inspect_evidence_metadata`, `link_evidence_to_task` | no evidence alteration, no raw secret display, no delete without review |
| `connectors` | Connector readiness and consent blockers | `inspect_connector_readiness`, `record_connector_blocker` | no OAuth wiring, no live read/write, no webhook handling |
| `model_local_readiness` | Local/provider readiness notes and blocked routes | `inspect_model_posture`, `record_model_notes` | no external model calls, no local model calls, no provider key entry |
| `governance` | Audit review posture and access-review blockers | `inspect_access_review`, `link_findings` | no breakglass, no secret reveal, no cross-tenant sharing |
| `runbooks` | Operator guidance and blocked remediation notes | `open_runbook`, `attach_runbook_reference` | no diagnostics, no automatic runbook execution, no scheduled checks |

## Downstream Consumer Expectations

- A downstream UI consumer may render headings, status labels, blocked actions, and metadata action labels.
- A downstream UI consumer must not infer executable buttons from `metadata_actions`.
- Any future action control requires a new migration gate with Guardian, approval, evidence, and rollback requirements.
- The inventory schema is `docs/contracts/schemas/arc_bot_phase1_business_inventory.schema.json`.
- The migration-gate packet is `tests/fixtures/arc_bot_phase1_business_inventory_migration_gate_packet.json`.

## Stop Conditions

Stop and request a new approval gate before adding:

- frontend routes or interactive UI state,
- persistence or customer data writes,
- connector read/write behavior,
- model/provider/local inference calls,
- worker dispatch or service control,
- approval enforcement or breakglass behavior,
- secret, token, credential, or raw evidence access.

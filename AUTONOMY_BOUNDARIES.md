# Arc Bot Autonomy Boundaries

Date: 2026-06-18
Status: Phase-0 guardrails

## What Arc Bot Shell Can Do (Now)

- Render contract-validated preview/control seam artifacts.
- Display blocked, review, and evidence-ready states.
- Aggregate read-only readiness posture.

## What Arc Bot Shell Must Not Do (Now)

- No autonomous execution.
- No automatic remediation.
- No connector/tool/file/network/robotics actions.
- No runtime secrets handling.

## What It May Do (With Explicit Approval in Later Phases)

- Dispatch queued work to approved worker lanes.
- Trigger model calls through approved routing.
- Invoke connector actions through approved policy gates.
- Persist and mutate task/work artifacts under audit.

## Governance Rule

Any move from preview to execution requires:

- explicit authority mode transition,
- proof of policy,
- approved execution token,
- audit/evidence continuity.

# Arc Bot LIMA Readiness Boundary

Branch status: `READY_FOR_ARC_READINESS_DOCS_AND_STATIC_PROOF_ONLY`

## Position

Arc Bot is **LIMA-ready**, not **LIMA-integrated**.

This means Arc Bot defines a future LIMA-boundary architecture and static proof of alignment, while production runtime behavior remains Arc-owned and Arc-authoritative.

- LIMA AI OS is a governed runtime dependency candidate for the future.
- Arc Guardian/execution boundaries remain Arc-owned until explicit runtime authority is approved.
- Arc does not route live office actions through LIMA in this branch.
- Arc does not route customer data, credentials, connector writes, file writes, browser actions, network actions, external sends, HumanInput bridge behavior, device actions, or automation through LIMA in this branch.
- All examples are dry-run/static and cannot be executed.

## Canonical status block

```text
READY_FOR_ARC_READINESS_DOCS_AND_STATIC_PROOF_ONLY
NOT_READY_FOR_RUNTIME_INTEGRATION
NOT_READY_FOR_LIMA_IMPORTS_IN_PRODUCT_CODE
NOT_READY_FOR_LIVE_OFFICE_ACTIONS_THROUGH_LIMA
NOT_READY_FOR_CONNECTORS_OR_CUSTOMER_DATA_THROUGH_LIMA
NOT_READY_FOR_HUMANINPUT_BRIDGE_BEHAVIOR
NOT_READY_FOR_DEVICE_OR_AUTOMATION_ACTIONS
```

## Readiness proof intent

This repo branch provides one proof packet:

- future call-shape sketch for LIMA interaction,
- normalized dry-run office task metadata examples,
- capability boundary expectations,
- approval boundary expectations.

No implementation is added.

## Hard constraints for this packet

- No product code runtime import/use of LIMA.
- No connector I/O.
- No workflow execution and no side effects.
- No provider/model calls.
- No model routing or model provider execution.
- No file system, terminal, browser, or network writes/reads as product actions.
- No scheduler/background execution.
- No worker dispatch.
- No secrets.

## Boundary ownership now

- Arc UI/state policy and execution authority: Arc-owned.
- Arc approvals and operator confirmations: Arc-owned.
- Arc evidence/audit linkage: Arc-owned and local to Arc proof posture.
- LIMA readiness: future seam documentation only.

## Next step

- Continue with `define-arc-bot-console-server-contract-schemas` after this branch is merged.

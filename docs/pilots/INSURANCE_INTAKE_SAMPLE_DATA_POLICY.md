# Insurance Intake Sample Data Policy

Date: 2026-06-21
Status: Phase-H/Phase-11 sample policy, runtime blocked

## Purpose

Set the sample-data boundary for the first Arc Bot pilot package.

## Allowed Sample Data

- Synthetic insurance intake metadata.
- Sanitized document IDs.
- Placeholder source refs such as `sample://...`.
- Redacted extraction preview refs.
- Operator-authored notes that contain no customer identifiers.

## Disallowed Sample Data

- Real customer documents.
- Real policy, claim, payment, HR, legal, medical, or identity data.
- Raw OCR text.
- Screenshots containing customer data.
- Provider prompts or model outputs from real customer content.
- Connector exports.
- Secrets, API keys, OAuth tokens, session tokens, or credentials.

## Handling Rules

- Keep sample payloads metadata-only.
- Do not commit raw customer content.
- Do not persist generated pilot output as final customer work.
- Do not use live connectors or model providers.
- Do not use cloud fallback.
- Treat every draft as pending operator review.

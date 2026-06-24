# Arc Intent Envelope Contract

Date: 2026-06-21
Status: Phase-B contract scaffold

## Purpose

`ArcIntentEnvelope` defines the future signed request boundary between Arc Bot
Shell and LIMA Office / Guardian. It is a metadata contract only in this repo.

## Current Authority

- Arc Bot Shell may build envelope projections.
- Arc Bot Shell may validate required metadata refs.
- Arc Bot Shell may preview the Guardian decision for the wrapped action.

## Blocked In This Phase

- No cryptographic signing.
- No signature verification claim by Arc Bot Shell.
- No approval token issuance.
- No runtime dispatch.
- No local model execution.
- No connector action.
- No customer-system mutation.

## Required Fields

- envelope ID,
- action ID,
- tenant ID,
- worker ID,
- operator ID,
- task ref,
- signature ref,
- policy refs,
- evidence refs,
- runbook refs,
- redaction policy ref,
- output policy ref,
- replay-protection ref.

## Future Owner

LIMA Office / Guardian must own signature verification, approval token lineage,
runtime authority acceptance, and replay protection before any execution path is
enabled.

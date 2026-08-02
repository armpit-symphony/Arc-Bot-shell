# Dependency pin lock

Every live dependency pin in Arc Bot Shell is declared once in
[`stack.lock.json`](../stack.lock.json). Nothing else is the source of truth.

## Why this exists

Arc's LIMA pin is written down in five places: `pyproject.toml`, both entries
in `workspace.lock.json`, the README, and the RC1 consumer attestation test.
Repeated incidents across this stack came from moving some copies and not
others.

The lock does not make a pin correct. It makes a pin one fact with one place
to change it, and turns disagreement into a build failure instead of a
discovery.

## What is and is not a pin

A **live pin** decides what a build, test, or install actually uses. Only
those are in the lock.

Commit hashes in `docs/proof_packets/`, `docs/audits/`, and `tests/fixtures/`
are **historical evidence** — a record of what was true when something was
attested. Around forty exist in this repository. They must never be rewritten
to match a current pin. The checker only visits paths the lock names, and a
test asserts no evidence path is registered as a site.

`ARC_V0_10_COMMIT` in `arc_bot_shell/service/config.py` is Arc's own rollback
target, not a dependency pin, and is deliberately not tracked here.

## The two checks

| | Consistency | Currency |
|---|---|---|
| Question | Do all copies of a pin agree? | Is the pin still the right one? |
| Needs network | No | Yes |
| Where | Every pull request, blocking | Scheduled weekday job |

Currency does not block pull requests. Whether LIMA merged something this
morning has nothing to do with whether the change under review is correct.

A pin can pass consistency and fail currency at once — that is exactly the
state behind the most recent incident in this stack.

## Policies

- `tracking` — expected to equal the dependency's `main`.
- `frozen` — deliberately held behind `main`. Requires a written reason, is
  reported but never failed by the currency job, and `bump-pin.py` refuses to
  move it without `--force`.

Arc's `lima-runtime` pin is **frozen** at the LIMA v0.1 RC1 public API freeze.
`tests/test_arc_lima_rc1_consumer_pin.py` attests that Arc consumes exactly
that commit. Arc does not need newer LIMA: the execution-grant path consumes
grants as JSON off the wire and imports nothing from `lima`. Moving it retires
that attestation and is a reviewed decision, never a routine bump.

## A known divergence, recorded on purpose

`LIMA_PINNED_COMMIT` in `arc_bot_shell/lima/lima_runtime_adapter.py` is the
v0.10 operator trust baseline. It is reported by `health.py` and
`integrations/doctor.py` and validated by `ArcOperatorConfig.__post_init__`.

It was last moved in `b62f119` and did not follow the install pin, so **Arc's
health output names an older LIMA commit than the one actually installed**.

It is registered in the lock as `lima-adapter-trust-baseline` rather than
quietly corrected, because changing the constant rejects every operator config
already persisted with the current value. That is a migration decision, not a
bump. Registering it means it cannot drift further without being noticed, and
a test fails if the divergence is closed without revisiting the recorded
reason.

## Moving a pin

```bash
python scripts/bump-pin.py guardian-suite --to main
python scripts/bump-pin.py lima-runtime --to <full-40-character-commit> --force
python scripts/check-stack-pins.py
```

The bumper rewrites only the captured commit characters and preserves each
file's existing line endings, so a pin move is a one-line diff per site.

## Adding a pin site

Add an entry under the dependency's `sites` with the path, a regex capturing a
group named `commit`, and the expected occurrence count. The pattern must
anchor on something identifying the dependency, because `workspace.lock.json`
holds more than one dependency's commit.

Any commit-shaped string in an `operational_paths` entry that is not
registered fails the build, so a new duplicate cannot appear quietly.

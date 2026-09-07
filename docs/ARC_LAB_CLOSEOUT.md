# Arc lab closeout and support contract

Lab baseline: 0.1.0-lab.4. Closeout changes are local candidates until released.

## Evidence already observed

On the original PC installation, two runs of the same 25 fixed synthetic
registration cases passed (50 attempts), with 28 mock review decisions.
These are deterministic fixture tests, not 50 independent model evaluations.
Qwen 2.5 7B drafted an SOP through Guardian and LIMA; the reviewed instruction
was saved separately. Restart restored practice state, SOPs and local evidence.
The operator reported that UI inputs and outputs worked in the manual pass.

This proves a bounded local training harness. It does not prove model weight
training, use of a saved SOP to generalize to unseen forms, public-site browser
automation, customer document processing, or a complete Office deployment.
The formal gate therefore continues to report mvp_complete=false.

## Windows lifecycle

The installed directory contains Start Arc.cmd, Restart Arc.cmd, Stop Arc.cmd,
Enable Arc at login.cmd and Disable Arc at login.cmd. Start/Restart opens the
UI at localhost port 8766 and enables the existing two local-model opt-ins.
Launching these controls is operator consent for the local model preview;
no tasks or model calls run automatically. Ollama and Qwen must already be
installed. Login startup is disabled by default and can be opted into using
the named control. It uses a per-user Startup shortcut without elevation.

The manager verifies process identity and sends a secret-bound graceful stop
request. It never force-kills another Python or Ollama process. Tokens stay
in a user-only ACL file and are excluded from exports. Launcher logs remain
under the install's data/runtime-harness directory. Starting twice is safe.

## Diagnostic export

POST /api/support/export requires training mode and the lab Guardian support
policy. The browser downloads a ZIP containing selected diagnostic counts,
build identity, and the chronological evidence index. Event payloads, paths,
SOP bodies, document contents, operator text, prompts and tokens are excluded.
It does not upload a bundle or export raw databases. The original audit data
stays local. This index is a support artifact, not a complete forensic backup.

## Synthetic reset

POST /api/support/reset requires training mode, an exact confirmation phrase,
and a Guardian allow decision. One transaction archives active registration
attempt/review rows and clears their visible counters. SOPs, work queues,
general task metrics and all audit events are preserved. Old attempt IDs
cannot be reviewed again. Archive tables remain in the local database for
recovery; reset is not a data-erasure or retention-policy control.

## Lab.5 qualification evidence

The public `0.1.0-lab.5` package was clean-installed from ZIP SHA-256
`2b4ea676c11d8f37ea60da893938fc4fd86c25f8c8dad13c1c7c512a9789a8d2`.
It selected Arc commit `72a5221bff908f5427eab5c7b10bea828ba75ddf`
with no modified-source marker. Exact-pin, one-worker Supervisor, execution
grant, restart, UI, Qwen detection, SOP restoration, and optional login
shortcut enable/disable checks passed.

A user-authorized Windows reboot was completed on 2026-09-06. With login
startup intentionally disabled, Arc correctly remained stopped after login.
The published Start lifecycle path then returned the loopback UI on port 8766.
The restored state contained 128 synthetic attempts, 31 reviews, and two SOPs;
Qwen was ready; the Supervisor classified one authenticated Arc worker as
healthy and eligible; and a new governed status request returned seven
redacted evidence events. Runtime execution and external side effects remained
false.

This closes the personal-PC reboot check. It is not production qualification,
customer-pilot approval, LAN exposure approval, connector approval, or
authorization for unattended execution.

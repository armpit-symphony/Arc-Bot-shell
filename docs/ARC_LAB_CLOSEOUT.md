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

## Qualification still needed

Record clean-install, launch, model detection, restart, SOP restoration and
login-shortcut results against the actual package. A process restart or direct
shortcut launch is not an OS reboot. Report the OS reboot check as pending
until a user-authorized reboot and subsequent login have actually occurred.
Office integration and production qualification are separate future work.

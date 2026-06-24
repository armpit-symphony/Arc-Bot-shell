Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$BaseTemp = Join-Path ([System.IO.Path]::GetTempPath()) (
  "arc_bot_phase2_handoff_guardrails_{0}" -f ([guid]::NewGuid().ToString("N"))
)

python -m pytest -q `
  tests/test_arc_bot_runtime_ui_scaffold_phase2_runtime_control.py `
  tests/test_arc_bot_runtime_ui_scaffold_runtime_control_consumer.py `
  tests/test_arc_bot_runtime_ui_scaffold_phase_chain.py `
  -p no:cacheprovider `
  --basetemp $BaseTemp

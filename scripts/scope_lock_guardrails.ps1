Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$BaseTemp = Join-Path ([System.IO.Path]::GetTempPath()) (
  "arc_bot_scope_lock_guardrails_{0}" -f ([guid]::NewGuid().ToString("N"))
)

python -m pytest -q `
  tests/test_arc_bot_runtime_ui_scaffold_phase_chain.py `
  tests/test_arc_bot_runtime_ui_scaffold_guardian_suite_seam.py `
  tests/test_arc_bot_phase0_scope_lock_runtime_ui.py `
  tests/test_arc_bot_runtime_ui_scaffold_contracts.py `
  -p no:cacheprovider `
  --basetemp $BaseTemp

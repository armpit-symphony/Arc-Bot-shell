Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$BaseTemp = Join-Path ([System.IO.Path]::GetTempPath()) (
  "arc_bot_phase1_handoff_guardrails_{0}" -f ([guid]::NewGuid().ToString("N"))
)

python -m pytest -q `
  tests/test_arc_bot_phase1_business_shell_inventory.py `
  tests/test_arc_bot_phase1_client_configuration_projection.py `
  tests/test_arc_bot_phase1_client_configuration_no_execution.py `
  tests/test_arc_bot_phase1_readiness_bundle.py `
  tests/test_arc_bot_phase1_readiness_bundle_packet.py `
  tests/test_arc_bot_phase1_runtime_authority_gating.py `
  -p no:cacheprovider `
  --basetemp $BaseTemp

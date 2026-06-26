Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$BaseTemp = Join-Path ([System.IO.Path]::GetTempPath()) (
  "arc_bot_worker_smoke_{0}" -f ([guid]::NewGuid().ToString("N"))
)

python -m phase0_runtime_ui_scaffold.phase_chain `
  --emit-status-snapshot `
  --with-guardian-suite-seam `
  --compact

python -m phase6_lima_office_integration.read_adapter --compact

python -m phase7_approval_evidence.readiness --compact

python -m phase7_approval_evidence.remaining_gate_response --compact

python -m phase10_field_deployment.package --compact

python -m phase11_pilot_readiness.pilot --compact

python -m phase12_mvp_completion.completion --compact

python -m phase12_mvp_completion.runtime_implementation_gate --compact

python -m pytest -q `
  tests/test_arc_field_deployment_package.py `
  tests/test_arc_pilot_readiness.py `
  tests/test_arc_mvp_completion_gate.py `
  tests/test_arc_runtime_implementation_gate.py `
  tests/test_arc_lima_office_read_adapter.py `
  tests/test_arc_approval_evidence_dependency.py `
  tests/test_arc_remaining_implementation_gate_response.py `
  -p no:cacheprovider `
  --basetemp $BaseTemp

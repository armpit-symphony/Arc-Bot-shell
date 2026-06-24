Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

python -m phase0_runtime_ui_scaffold.phase_chain `
  --emit-status-snapshot `
  --with-guardian-suite-seam `
  --status-snapshot-path tests/fixtures/arc_bot_runtime_ui_scaffold_phase0_scope_lock_status_snapshot.json `
  --compact

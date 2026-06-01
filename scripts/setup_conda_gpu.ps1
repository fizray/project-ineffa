# Compatibility wrapper. Prefer the hybrid all-in-one setup at repo root.

$rootSetup = Join-Path (Split-Path -Parent $PSScriptRoot) "setup_ineffa.ps1"
& $rootSetup -Mode gpu
exit $LASTEXITCODE

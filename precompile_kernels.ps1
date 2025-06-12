# Ouija Kernel Precompilation Script (for distribution/portable folder)
# This script does NOT build from source. It only precompiles kernels using the existing Ouija-CLI.exe.

$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot
$OuijaExe = Join-Path $ScriptDir "Ouija-CLI.exe"
$FiltersDir = Join-Path $ScriptDir "ouija_filters"

if (-not (Test-Path $OuijaExe)) {
    Write-Error "Ouija-CLI.exe not found in $ScriptDir. Cannot precompile kernels."
    exit 1
}

Write-Host "Precompiling main kernel..."
& $OuijaExe -n 0

Write-Host "Precompiling filter kernels..."
$filters = Get-ChildItem -Path $FiltersDir -Filter "ouija_*.cl"
foreach ($filter in $filters) {
    $name = $filter.BaseName
    Write-Host "Precompiling $name"
    & $OuijaExe -f $name -n 0
}

Write-Host "All kernels precompiled!"

[CmdletBinding()]
param([switch]$Verify, [switch]$Hardware, [int]$Port = 5000)
$ErrorActionPreference = 'Stop'
$backendRoot = Join-Path $PSScriptRoot 'backend'
$pythonPath = Join-Path $backendRoot '.venv/Scripts/python.exe'
$oldPythonPath = $env:PYTHONPATH
$oldHardware = $env:LAB_ALLOW_HARDWARE
Push-Location $backendRoot
try {
    if (-not (Test-Path -LiteralPath $pythonPath)) {
        python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the backend environment. Install Python 3.11 or newer.' }
    }
    $env:PYTHONPATH = ''
    $markerPath = Join-Path $backendRoot '.venv/workbench-installed'
    $requirementsHash = (Get-FileHash -LiteralPath 'requirements-workbench.txt').Hash
    if (-not (Test-Path -LiteralPath $markerPath) -or (Get-Content -LiteralPath $markerPath -Raw).Trim() -ne $requirementsHash) {
        & $pythonPath -m pip install -r requirements-workbench.txt
        if ($LASTEXITCODE -ne 0) { throw 'Backend dependency installation failed.' }
        Set-Content -LiteralPath $markerPath -Value $requirementsHash
    }
    if ($Verify) {
        & $pythonPath -m pytest tests/workbench -q
        if ($LASTEXITCODE -ne 0) { throw 'Backend tests failed.' }
    } else {
        if ($Hardware) { $env:LAB_ALLOW_HARDWARE = 'true' }
        Write-Host 'In the React app, choose Settings > Connect Flask backend.'
        & $pythonPath runserver.py --port $Port
        if ($LASTEXITCODE -ne 0) { throw 'Backend server failed.' }
    }
} finally {
    $env:PYTHONPATH = $oldPythonPath
    $env:LAB_ALLOW_HARDWARE = $oldHardware
    Pop-Location
}

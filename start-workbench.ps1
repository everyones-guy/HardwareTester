[CmdletBinding()]
param([switch]$Docker, [switch]$Verify)
$ErrorActionPreference = 'Stop'
$repoRoot = $PSScriptRoot
if ($Docker) {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Install and start Docker Desktop first.' }
    Push-Location $repoRoot
    try {
        docker info --format '{{.ServerVersion}}'
        if ($LASTEXITCODE -ne 0) { throw 'Docker engine is unavailable. Start Docker Desktop and try again.' }
        docker compose up --build -d
        if ($LASTEXITCODE -ne 0) { throw 'Docker Compose failed.' }
        Write-Host 'Hardware Tester: http://localhost:8080'
    } finally { Pop-Location }
    exit
}
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) { throw 'Install Node.js 22.12 or newer first.' }
Push-Location (Join-Path $repoRoot 'frontend')
try {
    if (-not (Test-Path -LiteralPath 'node_modules')) {
        npm.cmd ci --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    }
    if ($Verify) {
        npm.cmd test
        if ($LASTEXITCODE -ne 0) { throw 'Simulator tests failed.' }
        npm.cmd run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    } else {
        Write-Host 'Hardware Tester: http://localhost:5173'
        npm.cmd run dev
        if ($LASTEXITCODE -ne 0) { throw 'Workbench server failed.' }
    }
} finally { Pop-Location }

param([switch]$SkipBrowsers)
$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot
$previousPythonPath = $env:PYTHONPATH
$previousTemp = $env:TEMP
$previousTmp = $env:TMP
$previousReuse = $env:LAB_TEST_REUSE_SERVERS
function Invoke-Check {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Regression check failed: $Executable $Arguments" }
}
try {
    $env:PYTHONPATH = ''
    $env:LAB_TEST_REUSE_SERVERS = 'false'
    $env:TEMP = Join-Path $repo 'work/regression-temp'
    $env:TMP = $env:TEMP
    New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
    Push-Location (Join-Path $repo 'backend')
    try {
        Invoke-Check '.venv/Scripts/python.exe' @('-m','pytest','tests/workbench','-q')
        Invoke-Check '.venv/Scripts/python.exe' @('-m','black','--check','.')
    } finally { Pop-Location }
    Push-Location (Join-Path $repo 'frontend')
    try {
        Invoke-Check 'npm.cmd' @('run','format:check')
        Invoke-Check 'npm.cmd' @('test')
        Invoke-Check 'npm.cmd' @('run','build')
        if (-not $SkipBrowsers) {
            Invoke-Check 'npx.cmd' @('playwright','test','-c','playwright.regression.config.ts')
            Invoke-Check 'npx.cmd' @('playwright','test','-c','playwright.integration.config.ts')
            Invoke-Check 'npx.cmd' @('playwright','test','-c','playwright.auth.config.ts')
        }
    } finally { Pop-Location }
    Write-Host 'HardwareTester regression checks passed.'
} finally {
    $env:PYTHONPATH = $previousPythonPath
    $env:TEMP = $previousTemp
    $env:TMP = $previousTmp
    $env:LAB_TEST_REUSE_SERVERS = $previousReuse
}

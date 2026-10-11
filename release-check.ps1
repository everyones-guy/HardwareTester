# Disposable clean-install acceptance check. Requires Docker Desktop's Linux engine.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot
$runId = [guid]::NewGuid().ToString('N')
$sourceProject = "ht-release-$runId-source"
$targetProject = "ht-release-$runId-target"
$artifacts = Join-Path $repo "work/release-check/$runId"
$environmentFile = Join-Path $artifacts 'compose.env'
$owned = [System.Collections.Generic.List[string]]::new()
$cleanupFailed = $false
$names = @('LAB_HTTP_PORT', 'LAB_MQTT_PORT', 'LAB_API_TOKEN', 'LAB_AUTH_ENABLED', 'LAB_COOKIE_SECURE', 'LAB_ALLOW_HARDWARE')
$previous = @{}
foreach ($name in $names) { $previous[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }

function Invoke-Stack([string]$Project, [string[]]$Arguments) {
    & docker compose --env-file $environmentFile --project-directory $repo -f (Join-Path $repo 'docker-compose.yml') -p $Project @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose failed for $Project ($($Arguments[0]))." }
}

function Start-Disposable([string]$Project) {
    # A collision must never grant ownership of existing resources.
    $containers = @(Invoke-Stack $Project @('ps', '--all', '--quiet'))
    if ($containers.Count -gt 0) { throw "Project already exists: $Project" }
    $owned.Add($Project)
    Invoke-Stack $Project @('up', '--build', '-d', '--wait', '--wait-timeout', '180')
}

try {
    & docker info --format '{{.OSType}}' | ForEach-Object {
        if ($_ -ne 'linux') { throw 'Switch Docker Desktop to Linux containers.' }
    }
    if ($LASTEXITCODE -ne 0) { throw 'Docker API is unavailable. Start Docker Desktop and run this in a terminal with Docker access.' }
    New-Item -ItemType Directory -Force -Path $artifacts | Out-Null
    # Never read the production .env, including when PowerShell removes an empty variable.
    @('LAB_HTTP_PORT=0', 'LAB_MQTT_PORT=0', 'LAB_API_TOKEN=', 'LAB_AUTH_ENABLED=true', 'LAB_COOKIE_SECURE=false', 'LAB_ALLOW_HARDWARE=true') |
        Set-Content -LiteralPath $environmentFile -Encoding ascii
    # Docker allocates unused loopback ports; the check uses the private network.
    $env:LAB_HTTP_PORT = '0'
    $env:LAB_MQTT_PORT = '0'
    $env:LAB_API_TOKEN = ''
    $env:LAB_AUTH_ENABLED = 'true'
    $env:LAB_COOKIE_SECURE = 'false'
    $env:LAB_ALLOW_HARDWARE = 'true'

    Write-Host 'Building a fresh source installation (all four services must become healthy)...'
    Start-Disposable $sourceProject
    Invoke-Stack $sourceProject @('exec', '-T', 'backend', 'python', 'tools/release_check.py', 'seed', '--mqtt', '--web')

    # Restart every service, not just the backend, and wait for readiness again.
    Invoke-Stack $sourceProject @('stop')
    Invoke-Stack $sourceProject @('up', '-d', '--wait', '--wait-timeout', '180')
    Invoke-Stack $sourceProject @('exec', '-T', 'backend', 'python', 'tools/release_check.py', 'verify')
    $archive = Join-Path $artifacts 'workspace.json'
    Invoke-Stack $sourceProject @('cp', 'backend:/data/release-archive.json', $archive)

    Write-Host 'Recovering into a second fresh installation...'
    Start-Disposable $targetProject
    Invoke-Stack $targetProject @('cp', $archive, 'backend:/data/release-archive.json')
    Invoke-Stack $targetProject @('exec', '-T', 'backend', 'python', 'tools/release_check.py', 'restore', '--web')
    'PASS: build, healthy stack, first login, MQTT, validation, restart persistence, and independent recovery.' |
        Set-Content -LiteralPath (Join-Path $artifacts 'result.txt') -Encoding utf8
    Write-Host "Release check passed. Artifacts: $artifacts"
}
catch {
    if (Test-Path -LiteralPath $artifacts) {
        $_.Exception.Message | Set-Content -LiteralPath (Join-Path $artifacts 'failure.txt') -Encoding utf8
        foreach ($project in $owned) {
            & docker compose --env-file $environmentFile --project-directory $repo -f (Join-Path $repo 'docker-compose.yml') -p $project logs --no-color 2>&1 |
                Set-Content -LiteralPath (Join-Path $artifacts "$project.log") -Encoding utf8
        }
        Write-Host "Release check failed. Diagnostics: $artifacts"
    }
    throw
}
finally {
    # Only these randomly named projects belong to this invocation.
    foreach ($project in $owned) {
        & docker compose --env-file $environmentFile --project-directory $repo -f (Join-Path $repo 'docker-compose.yml') -p $project down --volumes --remove-orphans
        if ($LASTEXITCODE -ne 0) {
            $cleanupFailed = $true
            Write-Warning "Cleanup failed. Remove this test project with: docker compose -p $project down --volumes"
        }
    }
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name, $previous[$name], 'Process') }
}
if ($cleanupFailed) { throw 'Release checks passed, but Docker could not remove every disposable project. See the cleanup warning.' }

# PowerShell Script to Reset WSL Network and Assign a New IP

# Ensure PowerShell is running as Administrator
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Please run this script as Administrator!" -ForegroundColor Red
    Exit
}

Write-Host "Resetting WSL Network..." -ForegroundColor Cyan

# 1. Get the correct WSL network adapter name
$wslAdapter = Get-NetAdapter | Where-Object Name -Like "*WSL*" | Select-Object -ExpandProperty Name

if (-not $wslAdapter) {
    Write-Host "No WSL network adapter found! Exiting..." -ForegroundColor Red
    Exit
}

Write-Host "Detected WSL Adapter: $wslAdapter" -ForegroundColor Yellow

# 2. Disable WSL Network Adapter
Write-Host "Disabling $wslAdapter..."
Disable-NetAdapter -Name "$wslAdapter" -Confirm:$false

# 3. Release & Reset Windows Network Stack
Write-Host "Releasing and Renewing IP Addresses..."
ipconfig /release
ipconfig /flushdns
netsh winsock reset
netsh int ip reset

# 4. Re-enable WSL Network Adapter
Write-Host "Re-enabling $wslAdapter..."
Enable-NetAdapter -Name "$wslAdapter" -Confirm:$false

# 5. Shutdown WSL to Apply Changes
Write-Host "Shutting Down WSL..."
wsl --shutdown

# 6. Restart WSL
Write-Host "Restarting WSL..."
Start-Sleep -Seconds 5
wsl

# 7. Verify New IP Address
Write-Host "Checking New IP Address in WSL..."
wsl ip addr show eth0

Write-Host "WSL Network Reset Complete!" -ForegroundColor Green

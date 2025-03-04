# Set PowerShell to stop on errors
$ErrorActionPreference = "Stop"

Write-Host "=============================="
Write-Host "Universal Hardware Tester Setup (Windows)"
Write-Host "=============================="

# -------------------------------
# 1. Install WSL & Ubuntu
# -------------------------------
if (-Not (Get-Command wsl -ErrorAction SilentlyContinue)) {
    Write-Host "Installing WSL..."
    wsl --install
    Write-Host "WSL Installed. Restart your computer and run this script again."
    Exit
} else {
    Write-Host "WSL is already installed. Skipping..."
}

if (-Not (wsl --list --verbose | Select-String "Ubuntu-22.04")) {
    Write-Host "Installing Ubuntu 22.04 in WSL..."
    wsl --install -d Ubuntu-22.04
	Start-Sleep -Seconds 5  # Wait a few seconds to ensure install completes
    wsl -e exit  # Auto-exit WSL to continue setup
} else {
    Write-Host "Ubuntu-22.04 is already installed. Skipping..."
	Start-Sleep -Seconds 5  # Wait a few seconds to ensure install completes
    wsl -e exit  # Auto-exit WSL to continue setup
}

# -------------------------------
# 2. PostgreSQL Setup
# -------------------------------
$pgInstalled = Test-Path "C:\Program Files\PostgreSQL"
if (-Not $pgInstalled) {
    Write-Host "Installing PostgreSQL..."
    Invoke-WebRequest -Uri "https://get.enterprisedb.com/postgresql/postgresql-15.4-1-windows-x64.exe" -OutFile "postgres_installer.exe"
    Start-Process -FilePath "postgres_installer.exe" -ArgumentList "/S" -Wait
    Remove-Item "postgres_installer.exe"
} else {
    Write-Host "PostgreSQL is already installed. Skipping..."
}

# -------------------------------
# 3. Install Docker Desktop
# -------------------------------
if (-Not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Docker Desktop..."
    Invoke-WebRequest -Uri "https://desktop.docker.com/win/stable/Docker Desktop Installer.exe" -OutFile "docker_installer.exe"
    Start-Process -FilePath "docker_installer.exe" -ArgumentList "/quiet" -Wait
    Remove-Item "docker_installer.exe"
    Write-Host "Docker Installed. Please restart your computer and rerun this script."
    Exit
} else {
    Write-Host "Docker is already installed. Skipping..."
}

# -------------------------------
# 4. Install Kubernetes (kubectl)
# -------------------------------
if (-Not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Host "Installing kubectl..."
    Invoke-WebRequest -Uri "https://dl.k8s.io/release/v1.27.0/bin/windows/amd64/kubectl.exe" -OutFile "$env:ProgramFiles\kubectl.exe"
    [System.Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:ProgramFiles", [System.EnvironmentVariableTarget]::Machine)
} else {
    Write-Host "kubectl is already installed. Skipping..."
}

# -------------------------------
# 5. Install Minikube for Kubernetes
# -------------------------------
if (-Not (Get-Command minikube -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Minikube..."
    Invoke-WebRequest -Uri "https://storage.googleapis.com/minikube/releases/latest/minikube-windows-amd64.exe" -OutFile "$env:ProgramFiles\minikube.exe"
    [System.Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:ProgramFiles", [System.EnvironmentVariableTarget]::Machine
} else {
    Write-Host "Minikube is already installed. Skipping..."
}

# -------------------------------
# 6. Install AWS CLI
# -------------------------------
if (-Not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "Installing AWS CLI..."
    Invoke-WebRequest -Uri "https://awscli.amazonaws.com/AWSCLIV2.msi" -OutFile "AWSCLIV2.msi"
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/i AWSCLIV2.msi /quiet" -Wait
    Remove-Item "AWSCLIV2.msi"
} else {
    Write-Host "AWS CLI is already installed. Skipping..."
}

# -------------------------------
# 7. Clone GitHub Repository
# -------------------------------
$repoUrl = "https://github.com/your-username/universal-hardware-tester.git"
$repoDir = "$HOME\universal-hardware-tester"

if (-Not (Test-Path $repoDir)) {
    Write-Host "Cloning repository..."
    git clone $repoUrl $repoDir
} else {
    Write-Host "Repository already cloned. Pulling latest changes..."
    Set-Location $repoDir
    git pull origin main
}

Write-Host "**Setup complete! Your environment is ready.**"

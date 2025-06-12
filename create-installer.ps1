# Modern Installer Creation Script for Ouija
# This script installs NSIS and creates a professional Windows installer

param(
    [switch]$InstallNSIS,
    [switch]$CreateInstaller,
    [string]$Version = "0.3.14"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Ouija Modern Installer Creator" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Function to install NSIS via Chocolatey/Winget
function Install-NSIS {
    Write-Host "📦 Installing NSIS..." -ForegroundColor Yellow
    
    # Try winget first (modern package manager)
    try {
        Write-Host "Trying winget..." -ForegroundColor Cyan
        winget install NSIS.NSIS --silent --accept-source-agreements
        Write-Host "✅ NSIS installed via winget" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Winget failed, trying chocolatey..." -ForegroundColor Yellow
    }
    
    # Try chocolatey
    try {
        if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
            Write-Host "Installing Chocolatey first..." -ForegroundColor Cyan
            Set-ExecutionPolicy Bypass -Scope Process -Force
            [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
            iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        }
        
        choco install nsis -y
        Write-Host "✅ NSIS installed via chocolatey" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Chocolatey failed" -ForegroundColor Red
    }
    
    # Manual download as last resort
    Write-Host "📥 Downloading NSIS manually..." -ForegroundColor Yellow
    $nsisUrl = "https://sourceforge.net/projects/nsis/files/NSIS%203/3.10/nsis-3.10-setup.exe/download"
    $nsisInstaller = "$env:TEMP\nsis-setup.exe"
    
    try {
        Invoke-WebRequest -Uri $nsisUrl -OutFile $nsisInstaller -UseBasicParsing
        Start-Process -FilePath $nsisInstaller -ArgumentList "/S" -Wait
        Remove-Item $nsisInstaller -Force
        Write-Host "✅ NSIS installed manually" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Manual installation failed" -ForegroundColor Red
        Write-Host "Please install NSIS manually from: https://nsis.sourceforge.io/" -ForegroundColor Yellow
        return $false
    }
}

# Function to check if NSIS is available
function Test-NSIS {
    $nsisPath = Get-Command makensis -ErrorAction SilentlyContinue
    if ($nsisPath) {
        Write-Host "✅ NSIS found at: $($nsisPath.Source)" -ForegroundColor Green
        return $true
    }
    
    # Check common installation paths
    $commonPaths = @(
        "$env:ProgramFiles\NSIS\makensis.exe",
        "$env:ProgramFiles(x86)\NSIS\makensis.exe",
        "C:\Program Files\NSIS\makensis.exe",
        "C:\Program Files (x86)\NSIS\makensis.exe"
    )
    
    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            Write-Host "✅ NSIS found at: $path" -ForegroundColor Green
            $env:PATH += ";$(Split-Path $path)"
            return $true
        }
    }
    
    return $false
}

# Function to create the installer
function New-Installer {
    param($Version)
    
    Write-Host "🔨 Building NSIS installer..." -ForegroundColor Yellow
    
    # Check if distribution exists
    $distPath = "distribution\Ouija-v$Version-Windows"
    if (-not (Test-Path $distPath)) {
        Write-Host "❌ Distribution not found at: $distPath" -ForegroundColor Red
        Write-Host "Run .\build-release.ps1 first to create the distribution" -ForegroundColor Yellow
        return $false
    }
    
    # Update version in NSIS script
    $nsisContent = Get-Content "installer.nsi" -Raw
    $nsisContent = $nsisContent -replace '!define APP_VERSION ".*"', "!define APP_VERSION `"$Version`""
    Set-Content "installer.nsi" $nsisContent
      # Compile the installer
    try {
        $nsisOutput = & makensis installer.nsi 2>&1
        $nsisExitCode = $LASTEXITCODE
        
        if ($nsisExitCode -ne 0) {
            Write-Host "❌ NSIS compilation failed with exit code $nsisExitCode" -ForegroundColor Red
            Write-Host $nsisOutput -ForegroundColor Red
            return $false
        }
        
        $installerPath = "Ouija-v$Version-Setup.exe"
        if (Test-Path $installerPath) {
            $installerSize = (Get-Item $installerPath).Length
            Write-Host "✅ Installer created successfully!" -ForegroundColor Green
            Write-Host "   📄 File: $installerPath" -ForegroundColor White
            Write-Host "   📊 Size: $([math]::Round($installerSize / 1MB, 2)) MB" -ForegroundColor White
            
            # Move to distribution folder
            $finalPath = "distribution\Ouija-v$Version-Setup.exe"
            Move-Item $installerPath $finalPath -Force
            Write-Host "   📂 Moved to: $finalPath" -ForegroundColor White
            
            return $true
        }
        else {
            Write-Host "❌ Installer file not created" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ NSIS compilation failed: $_" -ForegroundColor Red
        return $false
    }
}

# Main execution
if ($InstallNSIS -or (-not (Test-NSIS))) {
    if (-not (Install-NSIS)) {
        Write-Host "❌ Failed to install NSIS" -ForegroundColor Red
        exit 1
    }
    
    # Refresh PATH
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
}

if (-not (Test-NSIS)) {
    Write-Host "❌ NSIS still not found after installation" -ForegroundColor Red
    exit 1
}

# Ensure success message is only printed if the installer creation succeeds
if ($CreateInstaller -or $PSBoundParameters.Count -eq 0) {
    $installerResult = New-Installer -Version $Version
    
    if ($installerResult) {
        Write-Host "" -ForegroundColor White
        Write-Host "🎉 Installer is ready for distribution" -ForegroundColor Green
        Write-Host "" -ForegroundColor White
    } else {
        Write-Host "❌ Installer creation failed. Please check the logs above." -ForegroundColor Red
        exit 1
    }
}

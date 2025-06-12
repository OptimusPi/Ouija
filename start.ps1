<#
.SYNOPSIS
Automated setup script for the Ouija project.
.DESCRIPTION
This script sets up the Python environment, installs dependencies, configures the C/OpenCL build, and runs the application.
#>

Write-Host "🚀 Starting automated setup for Ouija project..." -ForegroundColor Green

# Ensure the script always starts in the root directory
Set-Location -Path "$(Split-Path -Path $MyInvocation.MyCommand.Definition -Parent)"

# Step 1: Set up Python virtual environment
Write-Host "🔧 Setting up Python virtual environment..." -ForegroundColor Cyan
if (-Not (Test-Path ".venv")) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Failed to create virtual environment. Ensure Python is installed and in PATH."
        exit 1
    }
}
& .\.venv\Scripts\Activate.ps1
Write-Host "✅ Virtual environment activated."

# Step 2: Install Python dependencies
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Cyan
if (Test-Path "Ouija-ui\requirements.txt") {
    pip install --upgrade pip
    pip install -r Ouija-ui\requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Failed to install Python dependencies."
        exit 1
    }
    Write-Host "✅ Python dependencies installed."
} else {
    Write-Error "❌ requirements.txt not found in Ouija-ui. Cannot install dependencies."
    exit 1
}

# Step 3: Build the C/OpenCL project using the dedicated build script
Write-Host "🔨 Building C/OpenCL project..." -ForegroundColor Cyan
& "Ouija-cli\build.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Build failed. Check the output for errors."
    exit 1
}
Write-Host "✅ Build complete."

# Step 4: Copy Ouija-CLI.exe and lib folder to root directory
Write-Host "📋 Copying Ouija-CLI.exe and lib folder to root directory..." -ForegroundColor Cyan
if (Test-Path "Ouija-cli\Ouija-CLI.exe") {
    Copy-Item "Ouija-cli\Ouija-CLI.exe" "." -Force
    Write-Host "✅ Ouija-CLI.exe copied to root directory."
} else {
    Write-Error "❌ Ouija-CLI.exe not found in Ouija-cli directory."
    exit 1
}

if (Test-Path "Ouija-cli\lib") {
    if (Test-Path "lib") {
        Remove-Item "lib" -Recurse -Force
    }
    Copy-Item "Ouija-cli\lib" "." -Recurse -Force
    Write-Host "✅ lib folder copied to root directory."
} else {
    Write-Error "❌ lib folder not found in Ouija-cli directory."
    exit 1
}

# Also copy precompile_kernels.ps1 for kernel recompilation
if (Test-Path "Ouija-cli\precompile_kernels.ps1") {
    Copy-Item "Ouija-cli\precompile_kernels.ps1" "." -Force
    Write-Host "✅ precompile_kernels.ps1 copied to root directory."
} else {
    Write-Error "❌ precompile_kernels.ps1 not found in Ouija-cli directory."
    exit 1
}

# Step 5: Run the application
Write-Host "🚀 Running the application..." -ForegroundColor Green
if (Test-Path "Ouija-ui\app.py") {
    python "Ouija-ui\app.py"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Failed to run the application."
        exit 1
    }
} else {
    Write-Error "❌ app.py not found in Ouija-ui. Cannot launch the application."
    exit 1
}
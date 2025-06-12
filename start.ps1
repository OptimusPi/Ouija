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

# Step 3: Configure C/OpenCL build
Write-Host "🔨 Configuring C/OpenCL build..." -ForegroundColor Cyan
if (-Not (Test-Path "Ouija-cli\build")) {
    New-Item -ItemType Directory -Path "Ouija-cli\build" | Out-Null
}
cmake -S Ouija-cli -B Ouija-cli\build -DCMAKE_BUILD_TYPE=Release
if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ CMake configuration failed. Ensure CMake is installed and in PATH."
    exit 1
}
Write-Host "✅ CMake configuration complete."

# Step 4: Build the project
Write-Host "🔧 Building the project..." -ForegroundColor Cyan
cmake --build Ouija-cli\build --config Release
if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Build failed. Check the output for errors."
    exit 1
}
Write-Host "✅ Build complete."


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
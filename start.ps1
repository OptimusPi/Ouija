<#
.SYNOPSIS
Automated setup script for the Ouija project.
.DESCRIPTION
This script sets up the Python environment, installs dependencies, configures the C/OpenCL build, and runs the application.
#>

# Use script root for all paths, never change directory
$ScriptRoot = $PSScriptRoot

Write-Host "🚀 Starting automated setup for Ouija project..." -ForegroundColor Green

# Step 1: Set up Python virtual environment
Write-Host "🔧 Setting up Python virtual environment..." -ForegroundColor Cyan
$venvPath = Join-Path $ScriptRoot ".venv"
if (-Not (Test-Path $venvPath)) {
    python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Failed to create virtual environment. Ensure Python is installed and in PATH."
        exit 1
    }
}
& (Join-Path $venvPath "Scripts\Activate.ps1")
Write-Host "✅ Virtual environment activated."

# Step 2: Install Python dependencies
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Cyan
$requirements = Join-Path $ScriptRoot "Ouija-ui\requirements.txt"
if (Test-Path $requirements) {
    pip install --upgrade pip
    pip install -r $requirements
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Failed to install Python dependencies."
        exit 1
    }
    Write-Host "✅ Python dependencies installed."
} else {
    Write-Error "❌ requirements.txt not found in Ouija-ui. Cannot install dependencies."
    exit 1
}

# Check for required runtime files/folders in root
$required = @("Ouija-CLI.exe", "lib", "ouija_filters", "ouija_configs")
foreach ($item in $required) {
    if (-not (Test-Path (Join-Path $ScriptRoot $item))) {
        Write-Error "❌ Required file/folder missing in root: $item. Please run build.ps1 first."
        exit 1
    }
}

# Step 3: Build the C/OpenCL project using the dedicated build script
Write-Host "🔨 Building C/OpenCL project..." -ForegroundColor Cyan
$buildScript = Join-Path $ScriptRoot "Ouija-cli\build.ps1"
& $buildScript
if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Build failed. Check the output for errors."
    exit 1
}
Write-Host "✅ Build complete."

# Step 4: Run the application
Write-Host "🚀 Running the application..." -ForegroundColor Green
$appPy = Join-Path $ScriptRoot "Ouija-ui\app.py"
if (Test-Path $appPy) {
    Write-Host "💡 Tip: For best results in VS Code, select the .venv as your Python interpreter (Ctrl+Shift+P → Python: Select Interpreter)." -ForegroundColor Yellow
    python $appPy
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Failed to run the application."
        exit 1
    }
} else {
    Write-Error "❌ app.py not found in Ouija-ui. Cannot launch the application."
    exit 1
}
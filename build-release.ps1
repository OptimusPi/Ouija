# Ouija Complete Build Script for Windows Distribution
# This script builds both the CLI and UI components and creates a release package

$ErrorActionPreference = "Stop"

Write-Host "🔨 Ouija Complete Build Script v0.3.14" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$CLIDir = Join-Path $RootDir "Ouija-cli"
$UIDir = Join-Path $RootDir "Ouija-ui"
$DistDir = Join-Path $RootDir "distribution"

# Clean previous builds
Write-Host "🧹 Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path $DistDir) { Remove-Item $DistDir -Recurse -Force }
if (Test-Path (Join-Path $CLIDir "build")) { Remove-Item (Join-Path $CLIDir "build") -Recurse -Force }
if (Test-Path (Join-Path $UIDir "dist")) { Remove-Item (Join-Path $UIDir "dist") -Recurse -Force }
if (Test-Path (Join-Path $UIDir "build")) { Remove-Item (Join-Path $UIDir "build") -Recurse -Force }
Write-Host "✅ Clean complete" -ForegroundColor Green

# Create distribution directory
New-Item -ItemType Directory -Path $DistDir -Force | Out-Null

# Build CLI component
Write-Host "🔨 Building Ouija CLI..." -ForegroundColor Yellow

Push-Location $CLIDir
try {
    # Run the existing build script (no -PrecompileKernels here)
    & ".\build.ps1"
    
    if (-not (Test-Path ".\Ouija-CLI.exe")) {
        throw "CLI build failed - Ouija-CLI.exe not found"
    }
    
    Write-Host "✅ CLI build successful" -ForegroundColor Green
}
catch {
    Write-Host "❌ CLI build failed: $_" -ForegroundColor Red
    Pop-Location
    exit 1
}
finally {
    Pop-Location
}

# Build UI component  
Write-Host "🔨 Building Ouija UI..." -ForegroundColor Yellow

Push-Location $UIDir
try {
    # Check if Python is available
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        throw "Python not found in PATH. Please install Python 3.8+ and add it to PATH."
    }
    
    Write-Host "📦 Installing Python dependencies..." -ForegroundColor Cyan
    & python -m pip install --upgrade pip
    & python -m pip install -r requirements.txt
    & python -m pip install pyinstaller
    
    Write-Host "🔨 Building executable..." -ForegroundColor Cyan
    & python build_exe.py
    
    Write-Host "✅ UI build successful" -ForegroundColor Green
}
catch {
    Write-Host "❌ UI build failed: $_" -ForegroundColor Red
    Pop-Location
    exit 1
}
finally {
    Pop-Location
}

# Remove all .bin files from ouija_filters only before packaging
Write-Host "🧹 Removing all .bin files (OpenCL binaries) from ouija_filters..." -ForegroundColor Yellow
$FiltersDir = Join-Path $CLIDir "ouija_filters"
Get-ChildItem -Path $FiltersDir -Filter *.bin -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "✅ .bin files removed from ouija_filters" -ForegroundColor Green

# Create final distribution package
Write-Host "📦 Creating distribution package..." -ForegroundColor Yellow

$PackageDir = Join-Path $DistDir "Ouija-v0.3.14-Windows"
New-Item -ItemType Directory -Path $PackageDir -Force | Out-Null

# Copy CLI components
if (Test-Path (Join-Path $CLIDir "Ouija-CLI.exe")) {
    Copy-Item (Join-Path $CLIDir "Ouija-CLI.exe") (Join-Path $PackageDir "Ouija-CLI.exe") -Force
    Write-Host "✅ CLI executable copied" -ForegroundColor Green
    # Copy CLI lib directory if it exists (no nesting, just contents)
    $CLILib = Join-Path $CLIDir "lib"
    $DestLib = Join-Path $PackageDir "lib"
    if (Test-Path $CLILib) {
        if (-not (Test-Path $DestLib)) { New-Item -ItemType Directory -Path $DestLib | Out-Null }
        Copy-Item "$CLILib\*" $DestLib -Recurse -Force
        Write-Host "✅ CLI lib directory copied" -ForegroundColor Green
    } else {
        Write-Host "⚠️  CLI lib directory not found at $CLILib." -ForegroundColor Yellow
        exit 1
    }
    # Copy CLI ouija_filters directory if it exists
    $CLIFilters = Join-Path $CLIDir "ouija_filters"
    if (Test-Path $CLIFilters) {
        Copy-Item $CLIFilters (Join-Path $PackageDir "ouija_filters") -Recurse -Force
        Write-Host "✅ CLI ouija_filters directory copied" -ForegroundColor Green
    } else {
        Write-Host "⚠️  CLI ouija_filters directory not found at $CLIFilters." -ForegroundColor Yellow
        exit 1
    }
    # Copy ouija_search.cl (main kernel file)
    $MainKernel = Join-Path $CLIDir "lib\ouija_search.cl"
    if (Test-Path $MainKernel) {
        Copy-Item $MainKernel (Join-Path $PackageDir "lib\ouija_search.cl") -Force
        Write-Host "✅ Main kernel file (ouija_search.cl) copied" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Main kernel file not found at $MainKernel." -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "❌ Ouija-CLI.exe not found in CLI build output!" -ForegroundColor Red
    exit 1
}

# Copy UI components
$UIDistDir = Join-Path $UIDir "dist"
$OuijaUIExePath = Join-Path $UIDistDir "Ouija-UI.exe"

if (Test-Path $OuijaUIExePath) {
    Copy-Item $OuijaUIExePath (Join-Path $PackageDir "Ouija-UI.exe") -Force
    Write-Host "✅ UI executable copied as Ouija-UI.exe" -ForegroundColor Green
} else {
    Write-Host "❌ Ouija-UI.exe not found in $UIDistDir. UI build might have failed." -ForegroundColor Red
    exit 1
}

# Copy configs and databases
@("ouija_configs", "ouija_database") | ForEach-Object {
    $srcPath = Join-Path $RootDir $_
    $destPath = Join-Path $PackageDir $_
    if (Test-Path $srcPath) {
        if (-not (Test-Path $destPath)) { New-Item -ItemType Directory -Path $destPath | Out-Null }
        Get-ChildItem -Path $srcPath -Recurse | ForEach-Object {
            $target = Join-Path $destPath ($_.FullName.Substring($srcPath.Length).TrimStart('\','/'))
            if ($_.PSIsContainer) {
                if (-not (Test-Path $target)) { New-Item -ItemType Directory -Path $target | Out-Null }
            } else {
                Copy-Item $_.FullName $target -Force
            }
        }
    }
}

# Copy precompile_kernels.ps1 to the distribution package so the installer can offer kernel precompilation
Copy-Item (Join-Path $CLIDir "precompile_kernels.ps1") (Join-Path $PackageDir "precompile_kernels.ps1") -Force
Write-Host "✅ precompile_kernels.ps1 copied for installer kernel precompilation option" -ForegroundColor Green

# Copy user.ouija.conf as an example configuration
$UserConf = Join-Path $RootDir "user.ouija.conf"
if (Test-Path $UserConf) {
    Copy-Item $UserConf (Join-Path $PackageDir "user.ouija.conf") -Force
    Write-Host "✅ user.ouija.conf copied as example configuration" -ForegroundColor Green
} else {
    Write-Host "⚠️  user.ouija.conf not found at $UserConf" -ForegroundColor Yellow
}

# Copy icon file for NSIS installer
$IconFile = Join-Path $RootDir "icon.ouija.ico"
if (Test-Path $IconFile) {
    Copy-Item $IconFile (Join-Path $DistDir "icon.ouija.ico") -Force
    Write-Host "✅ Icon file copied for NSIS installer" -ForegroundColor Green
} else {
    Write-Host "⚠️  Icon file not found at $IconFile" -ForegroundColor Yellow
}

# Copy existing README.md instead of generating string-based garbage
$ReadmePath = Join-Path $RootDir "README.md"
if (Test-Path $ReadmePath) {
    Copy-Item $ReadmePath (Join-Path $PackageDir "README.md") -Force
    Write-Host "✅ README.md copied" -ForegroundColor Green
} else {
    Write-Host "⚠️  README.md not found" -ForegroundColor Yellow
}

# Create ZIP archive for distribution
$ZipPath = Join-Path $DistDir "Ouija-v0.3.14-Windows.zip"
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($PackageDir, $ZipPath)

if (!(Test-Path $ZipPath)) {
    Write-Host "❌ Failed to create ZIP archive. Build incomplete." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Distribution package created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📦 Package Details:" -ForegroundColor Cyan
Write-Host "   Directory: $PackageDir" -ForegroundColor White
Write-Host "   ZIP File:  $ZipPath" -ForegroundColor White
Write-Host "   Version:   0.3.14" -ForegroundColor White

# Calculate package size
$packageSize = (Get-ChildItem $PackageDir -Recurse | Measure-Object -Property Length -Sum).Sum
$zipSize = (Get-Item $ZipPath).Length

Write-Host ""
Write-Host "📊 Size Information:" -ForegroundColor Cyan
Write-Host "   Package: $([math]::Round($packageSize / 1MB, 2)) MB" -ForegroundColor White
Write-Host "   ZIP:     $([math]::Round($zipSize / 1MB, 2)) MB" -ForegroundColor White

Write-Host ""
Write-Host "🎉 Build Complete! Ready for distribution." -ForegroundColor Green
Write-Host "   Run create-installer.ps1 to create Ouija Installer executable." -ForegroundColor Yellow
Write-Host ""

# After the build process is complete, prompt the user to optionally create the installer
Write-Host "Would you like to build the installer as well? [Y/N]" -ForegroundColor Yellow
$response = Read-Host "Enter Y or N"
if ($response -eq "Y" -or $response -eq "y") {
    Write-Host "Running create-installer.ps1 to build the installer..." -ForegroundColor Cyan
    & .\create-installer.ps1
} else {
    Write-Host "Installer creation skipped. You can run create-installer.ps1 later if needed." -ForegroundColor Green
}

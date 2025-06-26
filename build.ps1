[CmdletBinding()]
param (
    [Switch]$Clean
)

$ErrorActionPreference = "Stop"

# Save the original directory
$origDir = Get-Location

try {
    $ScriptDir = $PSScriptRoot
    $BuildDir = Join-Path $ScriptDir "build"
    $OuijaExecutablePath = Join-Path $BuildDir "Release\\Ouija-CLI.exe" # Changed to Ouija-CLI.exe
    $FiltersDir = Join-Path $ScriptDir "ouija_filters"

    # Load version from version.ouija.txt
    $VersionFile = Join-Path $ScriptDir "version.ouija.txt"
    if (-not (Test-Path $VersionFile)) {
        Write-Host "ERROR: version.ouija.txt not found at $VersionFile" -ForegroundColor Red
        exit 1
    }
    $Version = Get-Content $VersionFile | Select-Object -First 1
    Write-Host "Loaded version: $Version"

    Write-Host "Build script started..."
    Write-Host "Workspace Root: $ScriptDir"
    Write-Host "Build Directory: $BuildDir"
    if ($Clean) { Write-Host "Clean build requested." }

    # 1. Clean Build Directory (if -Clean is specified)
    if ($Clean) {
        if (Test-Path $BuildDir) {
            Write-Host "Cleaning build directory: $BuildDir"
            Remove-Item -Recurse -Force $BuildDir
            Write-Host ""
        } else {
            Write-Host "Build directory does not exist, no need to clean."
        }
        Write-Host ""

        # Clean ouija_search.bin from lib folder
        $mainKernelBin = Join-Path $ScriptDir "lib\ouija_search.bin"
        if (Test-Path $mainKernelBin) {
            Write-Host "Removing main kernel binary: $mainKernelBin"
            Remove-Item -Force $mainKernelBin
            Write-Host ""
        } else {
            Write-Host "Main kernel binary not found, no need to clean: $mainKernelBin"
        }
        Write-Host ""

        # Clean all ouija_*.bin files from filters directory
        $filterBinFiles = Get-ChildItem -Path $FiltersDir -Filter "ouija_*.bin"
        if ($filterBinFiles) {
            Write-Host "Removing filter kernel binaries from: $FiltersDir"
            foreach ($binFile in $filterBinFiles) {
                Write-Host "  Removing $($binFile.FullName)"
                Remove-Item -Force $binFile.FullName
            }
        }
    }

    # 2. Create Build Directory if it doesn't exist
    if (-not (Test-Path $BuildDir)) {
        Write-Host "Creating build directory: $BuildDir"
        New-Item -ItemType Directory -Path $BuildDir | Out-Null
    }

    # 3. Configure and Build (CMake example)
    Write-Host "Configuring and building in build directory: $BuildDir"

    try {
        Write-Host "Configuring project with CMake..."
        cmake -S "$ScriptDir" -B "$BuildDir"  # Configure from root, output to build dir

        Write-Host "Building project (Release configuration)..."
        cmake --build "$BuildDir" --config Release
        # For MSBuild directly if you have a solution (adjust path/name as needed):
        # msbuild Ouija.sln /p:Configuration=Release

        $ouijaExeSource = Join-Path $BuildDir "Release" "Ouija-CLI.exe" # Changed to Ouija-CLI.exe
        if (Test-Path $ouijaExeSource) {
            $ouijaExeTarget = Join-Path $ScriptDir "Ouija-CLI.exe" # Changed to Ouija-CLI.exe
            Copy-Item -Path $ouijaExeSource -Destination $ouijaExeTarget -Force
            Write-Host "Build completed successfully."
        } else {
            Write-Error "Ouija-CLI.exe not found at $ouijaExeSource. Build might have failed."
            exit 1
        }

    } catch {
        Write-Error "Build process failed: $($_.Exception.Message)"
        exit 1
    }

    Write-Host "✅ Build script finished."
    Write-Host ""

} finally {
    Set-Location $origDir
}

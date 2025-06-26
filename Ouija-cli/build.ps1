[CmdletBinding()]
param (
    [Switch]$Clean,
    [Switch]$PrecompileKernels
)

$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot
$BuildDir = Join-Path $ScriptDir "build"
$OuijaExecutablePath = Join-Path $BuildDir "Release\\Ouija-CLI.exe" # Changed to Ouija-CLI.exe
$FiltersDir = Join-Path $ScriptDir "..\ouija_filters"

# Read version from version.ouija.txt
$Version = Get-Content "$PSScriptRoot\..\version.ouija.txt" | Select-Object -First 1

Write-Host "Build script started..."
Write-Host "Workspace Root: $ScriptDir"
Write-Host "Build Directory: $BuildDir"
if ($Clean) { Write-Host "Clean build requested." }
if ($PrecompileKernels) { Write-Host "Kernel pre-compilation requested after build." }

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
Write-Host "Navigating to build directory: $BuildDir"

try {
    Write-Host "Configuring project with CMake..."
    cmake -S "$ScriptDir" -B "$BuildDir"  # Configure from root, output to build dir
    Write-Host "Building project (Release configuration)..."
    cmake --build "$BuildDir" --config Release
    $ouijaExeSource = Join-Path $BuildDir "Release" "Ouija-CLI.exe"
    if (Test-Path $ouijaExeSource) {
        $ouijaExeTarget = Join-Path $ScriptDir "Ouija-CLI.exe"
        Copy-Item -Path $ouijaExeSource -Destination $ouijaExeTarget -Force
        Write-Host "Build completed successfully."
    } else {
        Write-Error "Ouija-CLI.exe not found at $ouijaExeSource. Build might have failed."
        exit 1
    }


    # 4. Precompile Kernels (if -PrecompileKernels is specified and build was successful)
    if ($PrecompileKernels) {
        Write-Host "Pre-compiling OpenCL kernels..."
        $sourceExePath = Join-Path $BuildDir "Release" "Ouija-CLI.exe" # Changed to Ouija-CLI.exe
        
        if (-not (Test-Path $sourceExePath)) {
            Write-Error "Ouija-CLI.exe not found at $sourceExePath. Build might have failed. Cannot pre-compile kernels."
        } else {
            $ouijaExeInRootDir = Join-Path $PSScriptRoot "Ouija-CLI.exe" # Changed to Ouija-CLI.exe
            try {
                Write-Host "Copying $sourceExePath to $ouijaExeInRootDir for pre-compilation."
                Copy-Item -Path $sourceExePath -Destination $ouijaExeInRootDir -Force
                Write-Host "--------------------------------------------------"
                Write-Host "Starting parallel pre-compilation of Ouija filter kernels (ouija_*.cl)..."
                Write-Host "Ouija executable for filters: $ouijaExeInRootDir"
                $filtersSourceDir = Join-Path $PSScriptRoot "..\ouija_filters"
                Write-Host "Filters directory: $filtersSourceDir"
                Write-Host "--------------------------------------------------"

                $filterFiles = Get-ChildItem -Path $filtersSourceDir -Filter "ouija_*.cl"
                $jobs = @()
                foreach ($file in $filterFiles) {
                    $filterName = $file.BaseName
                    $scriptBlock = {
                        param($currentCopiedExePath, $currentFilterName)
                        $filterCommandArgs = @("-f", $currentFilterName, "-n", "0") # Compile-only mode
                        Write-Host "Starting job for filter: $currentFilterName"
                        try {
                            $stdoutFile = "filter_${currentFilterName}_stdout.txt"
                            $stderrFile = "filter_${currentFilterName}_stderr.txt"
                            $process = Start-Process -FilePath $currentCopiedExePath -ArgumentList $filterCommandArgs -Wait -PassThru -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile -NoNewWindow
                            $stdout = Get-Content $stdoutFile -Raw 2>$null
                            $stderr = Get-Content $stderrFile -Raw 2>$null
                            
                            if ($process.ExitCode -ne 0) {
                                $errorMsg = "Filter '$currentFilterName' compilation failed with exit code $($process.ExitCode)"
                                if ($stderr) {
                                    $errorMsg += "`nSTDERR: $stderr"
                                }
                                if ($stdout) {
                                    $errorMsg += "`nSTDOUT: $stdout"
                                }
                                throw $errorMsg
                            } else {
                                Write-Host "Filter '$currentFilterName' compilation completed successfully"
                                if ($stdout) {
                                    Write-Host "STDOUT: $stdout"
                                }
                            }
                        } finally {
                            # Clean up temporary files
                            Remove-Item $stdoutFile -ErrorAction SilentlyContinue
                            Remove-Item $stderrFile -ErrorAction SilentlyContinue
                        }
                    }
                    $jobs += Start-Job -ScriptBlock $scriptBlock -ArgumentList $ouijaExeInRootDir, $filterName
                }

                Write-Host "Waiting for all kernel compilation jobs to complete..."
                $hasErrors = $false
                foreach ($job in $jobs) {
                    $jobResult = Wait-Job $job | Receive-Job
                    if ($job.State -eq "Failed") {
                        $hasErrors = $true
                        Write-Error "Compilation job failed: $($job.ChildJobs[0].JobStateInfo.Reason.Message)"
                    } elseif ($jobResult) {
                        Write-Host $jobResult
                    }
                }
                
                if ($hasErrors) {
                    throw "One or more kernel compilation jobs failed. Check the error messages above for details."
                }
                
                Write-Host "All kernel compilation jobs finished successfully."

            } catch {
                Write-Error "An error occurred during the pre-compilation process: $($_.Exception.Message)"
            }
        }
        Write-Host "Kernel pre-compilation section finished."
    }

} catch {
    Write-Error "Build process failed: $($_.Exception.Message)"
    exit 1
}

Write-Host "✅ Build script finished."
Write-Host ""

# Example for MSVC (cl.exe):
# $compileFlags = "/D OUIJA_VERSION=\"$Version\" ...other flags..."
# cl.exe $compileFlags ...

# Example for GCC/Clang:
# $compileFlags = "-DOUIJA_VERSION=\"$Version\" ...other flags..."
# gcc $compileFlags ...

# If using CMake, add -DOUIJA_VERSION=\"$Version\" to CMAKE_C_FLAGS or as a -D argument:
# cmake -DOUIJA_VERSION=$Version ...

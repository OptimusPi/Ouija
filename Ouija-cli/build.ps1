[CmdletBinding()]
param (
    [Switch]$Clean,
    [Switch]$PrecompileKernels
)

$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot
$BuildDir = Join-Path $ScriptDir "build"
$OuijaExecutablePath = Join-Path $BuildDir "Release\\Ouija-CLI.exe" # Changed to Ouija-CLI.exe
$FiltersDir = Join-Path $ScriptDir "ouija_filters"

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
Push-Location $BuildDir

try {
    Write-Host "Configuring project with CMake..."
    cmake ..  # Assumes CMakeLists.txt is in $ScriptDir (parent of $BuildDir)
              # Add generator if needed, e.g., cmake .. -G "Visual Studio 17 2022"

    Write-Host "Building project (Release configuration)..."
    cmake --build . --config Release
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


    # 4. Precompile Kernels (if -PrecompileKernels is specified and build was successful)
    if ($PrecompileKernels) {
        # This block should be correctly placed after the build commands.
        # Ensure current directory is the script's root directory ($ScriptDir or $PSScriptRoot)
        # If the build happens in a different location, ensure you are back in the root.
        # The Pop-Location / Push-Location logic from your previous script version is good here.
        if ($PWD.Path -eq $BuildDir) {
            Pop-Location # Go back to $ScriptDir from $BuildDir
        }
        Push-Location $PSScriptRoot # Ensure we are in the script's root directory

        Write-Host "Pre-compiling OpenCL kernels..."
        $sourceExePath = Join-Path $BuildDir "Release" "Ouija-CLI.exe" # Changed to Ouija-CLI.exe
        
        if (-not (Test-Path $sourceExePath)) {
            Write-Error "Ouija-CLI.exe not found at $sourceExePath. Build might have failed. Cannot pre-compile kernels."
        } else {
            $ouijaExeInRootDir = Join-Path $PSScriptRoot "Ouija-CLI.exe" # Changed to Ouija-CLI.exe
            try {
                Write-Host "Copying $sourceExePath to $ouijaExeInRootDir for pre-compilation."
                Copy-Item -Path $sourceExePath -Destination $ouijaExeInRootDir -Force
                
                # --- Main Kernel Pre-compilation (Parallel with filters) ---
                Write-Host "--------------------------------------------------"
                Write-Host "Pre-compiling main kernel: lib\ouija_search.cl (in parallel with filters)"
                Write-Host "Ouija executable for main kernel: $ouijaExeInRootDir"
                Write-Host "--------------------------------------------------"
                $jobs = @()                # Add main kernel job
                $mainKernelScriptBlock = {
                    param($currentCopiedExePath)
                    $mainKernelArgs = @("-n", "0")
                    Write-Host "Starting job for main kernel: lib\ouija_search.cl"
                    try {
                        $process = Start-Process -FilePath $currentCopiedExePath -ArgumentList $mainKernelArgs -Wait -PassThru -RedirectStandardOutput "main_kernel_stdout.txt" -RedirectStandardError "main_kernel_stderr.txt" -NoNewWindow
                        $stdout = Get-Content "main_kernel_stdout.txt" -Raw 2>$null
                        $stderr = Get-Content "main_kernel_stderr.txt" -Raw 2>$null
                        
                        if ($process.ExitCode -ne 0) {
                            $errorMsg = "Main kernel compilation failed with exit code $($process.ExitCode)"
                            if ($stderr) {
                                $errorMsg += "`nSTDERR: $stderr"
                            }
                            if ($stdout) {
                                $errorMsg += "`nSTDOUT: $stdout"
                            }
                            throw $errorMsg
                        } else {
                            Write-Host "Main kernel compilation completed successfully"
                            if ($stdout) {
                                Write-Host "STDOUT: $stdout"
                            }
                        }
                    } finally {
                        # Clean up temporary files
                        Remove-Item "main_kernel_stdout.txt" -ErrorAction SilentlyContinue
                        Remove-Item "main_kernel_stderr.txt" -ErrorAction SilentlyContinue
                    }
                }
                $jobs += Start-Job -ScriptBlock $mainKernelScriptBlock -ArgumentList $ouijaExeInRootDir

                # --- Filter Kernels Pre-compilation (Parallel) ---
                Write-Host "--------------------------------------------------"
                Write-Host "Starting parallel pre-compilation of Ouija filter kernels (ouija_*.cl)..."
                Write-Host "Ouija executable for filters: $ouijaExeInRootDir"
                $filtersSourceDir = Join-Path $PSScriptRoot "ouija_filters"
                Write-Host "Filters directory: $filtersSourceDir"
                Write-Host "--------------------------------------------------"

                $filterFiles = Get-ChildItem -Path $filtersSourceDir -Filter "ouija_*.cl"

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
                            Remove-Item "filter_${currentFilterName}_stdout.txt" -ErrorAction SilentlyContinue
                            Remove-Item "filter_${currentFilterName}_stderr.txt" -ErrorAction SilentlyContinue
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
        Pop-Location # Match the Push-Location $PSScriptRoot
        Write-Host "Kernel pre-compilation section finished."
    }

} catch {
    Write-Error "Build process failed: $($_.Exception.Message)"
    exit 1
} finally {
    if ($PWD.Path -eq $BuildDir) {
        Pop-Location
    }
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

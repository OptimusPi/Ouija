# Ouija NSIS Installer Script
# Requires NSIS (Nullsoft Scriptable Install System) to be installed

!define APP_NAME "Ouija"
!define APP_VERSION "0.3.14"
!define APP_PUBLISHER "OptimusPi (pifreak loves you!)"
!define APP_URL "https://github.com/OptimusPi/ouija"
!define APP_SUPPORT_URL "https://github.com/OptimusPi/ouija/issues"

# Installer settings
Name "${APP_NAME} v${APP_VERSION}"
OutFile "Ouija-v${APP_VERSION}-Setup.exe"
InstallDir "$PROGRAMFILES64\${APP_NAME}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "InstallDir"
RequestExecutionLevel admin

# Modern UI
!include "MUI2.nsh"
!include "x64.nsh"

# Interface settings
!define MUI_ABORTWARNING
# Icon is optional - comment out if not available
!define MUI_ICON "icon.ouija.ico"
!define MUI_UNICON "icon.ouija.ico"

# Pages
!insertmacro MUI_PAGE_WELCOME
# !insertmacro MUI_PAGE_LICENSE "LICENSE"  # Optional - uncomment if LICENSE file exists at root
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

# Finish page with options
!define MUI_FINISHPAGE_RUN "$INSTDIR\Ouija-UI.exe"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.md"
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED

# Add kernel precompilation checkbox option
!define MUI_FINISHPAGE_RUN_FUNCTION "LaunchApplication"
!define MUI_FINISHPAGE_RUN_TEXT "Start ${APP_NAME}"
!define MUI_FINISHPAGE_RUN_NOTCHECKED
!define MUI_FINISHPAGE_CHECKBOX
!define MUI_FINISHPAGE_CHECKBOX_TEXT "Precompile OpenCL kernels for faster startup (recommended)"
!define MUI_FINISHPAGE_CHECKBOX_CHECKED
!define MUI_FINISHPAGE_FUNCTION_CHECKBOX "RunKernelPrecompilation"

!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

# Languages
!insertmacro MUI_LANGUAGE "English"

# Version info
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey "FileDescription" "Balatro Seed Finder"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "LegalCopyright" "© 2025 ${APP_PUBLISHER}"

# Installer sections
Section "Core Application" SecCore
    SectionIn RO  # Required section
    SetOutPath "$INSTDIR"
    # Core files
    File "/oname=Ouija-UI.exe" "distribution\Ouija-v${APP_VERSION}-Windows\Ouija-UI.exe"
    File "/oname=Ouija-CLI.exe" "distribution\Ouija-v${APP_VERSION}-Windows\Ouija-CLI.exe"
    File "/oname=README.md" "distribution\Ouija-v${APP_VERSION}-Windows\README.md"
    File "/oname=user.ouija.conf" "distribution\Ouija-v${APP_VERSION}-Windows\user.ouija.conf"
    File "/oname=build.ps1" "distribution\Ouija-v${APP_VERSION}-Windows\build.ps1"
    # Directories
    SetOutPath "$INSTDIR\lib"
    File /r "distribution\Ouija-v${APP_VERSION}-Windows\lib\*.*"
    SetOutPath "$INSTDIR\ouija_filters"
    File /r "distribution\Ouija-v${APP_VERSION}-Windows\ouija_filters\*.*"
    SetOutPath "$INSTDIR\ouija_configs"
    File /r "distribution\Ouija-v${APP_VERSION}-Windows\ouija_configs\*.*"
    # Create simple kernel precompilation batch file that just calls build.ps1
    FileOpen $0 "$INSTDIR\precompile_kernels.cmd" w
    FileWrite $0 "@echo off$\r$\n"
    FileWrite $0 "title Ouija OpenCL Kernel Precompilation$\r$\n"
    FileWrite $0 "echo ======================================================$\r$\n"
    FileWrite $0 "echo        Ouija OpenCL Kernel Precompilation Tool$\r$\n"
    FileWrite $0 "echo ======================================================$\r$\n"
    FileWrite $0 "echo.$\r$\n"
    FileWrite $0 "echo This process will improve Ouija's startup performance$\r$\n"
    FileWrite $0 "echo by precompiling all OpenCL kernels for your GPU.$\r$\n"
    FileWrite $0 "echo.$\r$\n"
    FileWrite $0 "cd /d $\"$INSTDIR$\"$\r$\n"
    FileWrite $0 "echo Checking GPU compatibility...$\r$\n"
    FileWrite $0 "$\"$INSTDIR\Ouija-CLI.exe$\" --list_devices$\r$\n"
    FileWrite $0 "if %ERRORLEVEL% neq 0 ($\r$\n"
    FileWrite $0 "  echo.$\r$\n"
    FileWrite $0 "  echo ERROR: No compatible OpenCL GPU detected.$\r$\n"
    FileWrite $0 "  echo Please update your graphics drivers and try again.$\r$\n"
    FileWrite $0 "  echo.$\r$\n"
    FileWrite $0 "  pause$\r$\n"
    FileWrite $0 "  exit /b 1$\r$\n"
    FileWrite $0 ")$\r$\n"
    FileWrite $0 "echo.$\r$\n"
    FileWrite $0 "echo Running kernel precompilation using build.ps1...$\r$\n"
    FileWrite $0 "powershell -ExecutionPolicy Bypass -NoProfile -Command $\"& '$INSTDIR\build.ps1' -PrecompileKernels$\"$\r$\n"
    FileWrite $0 "echo.$\r$\n"
    FileWrite $0 "echo ======================================================$\r$\n"
    FileWrite $0 "echo       Kernel precompilation process completed!$\r$\n"
    FileWrite $0 "echo     Ouija will now start faster on your system.$\r$\n"
    FileWrite $0 "echo ======================================================$\r$\n"
    FileWrite $0 "echo.$\r$\n"
    FileWrite $0 "pause$\r$\n"
    FileClose $0
    
    # Registry entries
    WriteRegStr HKLM "Software\${APP_NAME}" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\${APP_NAME}" "Version" "${APP_VERSION}"
    
    # Uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
      # Add/Remove Programs entry
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "URLInfoAbout" "${APP_URL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "HelpLink" "${APP_SUPPORT_URL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "InstallLocation" "$INSTDIR"
    # Copy icon to Windows dir for Add/Remove Programs
    SetOutPath "$INSTDIR"
    File "/oname=icon.ico" "icon.ouija.ico"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" "$INSTDIR\icon.ico"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoRepair" 1
SectionEnd

Section "Desktop Shortcut" SecDesktop
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\Ouija-UI.exe" "" "$INSTDIR\Ouija-UI.exe" 0
SectionEnd

Section "Start Menu Shortcuts" SecStartMenu
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\Ouija-UI.exe"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME} CLI.lnk" "$INSTDIR\Ouija-CLI.exe"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\README.lnk" "$INSTDIR\README.md"
    CreateShortCut "$SMPadROGRAMS\${APP_NAME}\Precompile OpenCL Kernels.lnk" "$INSTDIR\precompile_kernels.cmd" "" "$INSTDIR\icon.ico"
SectionEnd

Section "Sample Database" SecDatabase
    # Create separate directories to fix nesting issue
    SetOutPath "$INSTDIR\ouija_database"
    File /r "distribution\Ouija-v${APP_VERSION}-Windows\ouija_database\*.duckdb"
    
    # Ensure configs are in their own directory, not nested inside the database folder
    SetOutPath "$INSTDIR\ouija_configs"
    File /r "distribution\Ouija-v${APP_VERSION}-Windows\ouija_configs\*.json"
SectionEnd

# Component descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} "Core application files (required)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "Create a desktop shortcut"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} "Create Start Menu shortcuts"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDatabase} "Include sample database files"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

# Installer functions
Function .onInit
    # Check if running on 64-bit Windows
    ${IfNot} ${RunningX64}
        MessageBox MB_OK|MB_ICONSTOP "This application requires 64-bit Windows."
        Abort
    ${EndIf}
    
    # Check for existing installation
    ReadRegStr $0 HKLM "Software\${APP_NAME}" "InstallDir"
    ${If} $0 != ""
        MessageBox MB_YESNO|MB_ICONQUESTION "${APP_NAME} is already installed. Do you want to continue?" IDYES continue
        Abort
        continue:
    ${EndIf}
FunctionEnd

Function .onInstSuccess
    # Check OpenCL support after installation
    ExecWait '"$INSTDIR\Ouija-CLI.exe" --list_devices' $0
    ${If} $0 != 0
        MessageBox MB_OK|MB_ICONINFORMATION "Installation complete!$\n$\nNote: OpenCL GPU support was not detected. You may need to update your graphics drivers for optimal performance."
    ${Else}
        # Offer to precompile OpenCL kernels
        MessageBox MB_YESNO|MB_ICONQUESTION "GPU support detected! Would you like to precompile OpenCL kernels now for faster startup? This may take a minute but will improve first-run performance." IDNO skipPrecompilation
            DetailPrint "Precompiling OpenCL kernels..."
            SetDetailsPrint both
            ExecWait '"$INSTDIR\Ouija-CLI.exe" -n 0' $1
            # Precompile all filter templates
            FindFirst $2 $3 "$INSTDIR\ouija_filters\ouija_*.cl"
            loop:
                StrCmp $3 "" done
                ${If} $3 != ""
                    # Extract template name without extension and path
                    StrCpy $4 $3 -3 # Remove .cl extension
                    DetailPrint "Precompiling filter: $4"
                    ExecWait '"$INSTDIR\Ouija-CLI.exe" -f $4 -n 0' $1
                ${EndIf}
                FindNext $2 $3
                Goto loop
            done:
            FindClose $2
            SetDetailsPrint none
            MessageBox MB_OK|MB_ICONINFORMATION "Installation complete!$\n$\nGPU support detected and kernels precompiled. ${APP_NAME} is ready to use."
            Goto endFunction
        skipPrecompilation:
            MessageBox MB_OK|MB_ICONINFORMATION "Installation complete!$\n$\nGPU support detected. ${APP_NAME} is ready to use."
    ${EndIf}
    endFunction:
FunctionEnd

# Function RunAdvancedPrecompile has been replaced by RunKernelPrecompilation

# Uninstaller
Section "Uninstall"    # Remove files
    Delete "$INSTDIR\Ouija-UI.exe"
    Delete "$INSTDIR\Ouija-CLI.exe"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\LICENSE"
    Delete "$INSTDIR\Uninstall.exe"
    Delete "$INSTDIR\build.ps1"
    Delete "$INSTDIR\precompile_kernels.ps1"
    Delete "$INSTDIR\precompile_kernels.cmd"
    Delete "$INSTDIR\icon.ico"
      # Remove directories
    RMDir /r "$INSTDIR\lib"
    RMDir /r "$INSTDIR\ouija_filters"
    RMDir /r "$INSTDIR\ouija_configs"
    RMDir /r "$INSTDIR\ouija_database"
    
    # Remove shortcuts
    Delete "$DESKTOP\${APP_NAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APP_NAME}"
    
    # Remove registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
    DeleteRegKey HKLM "Software\${APP_NAME}"
    
    # Remove installation directory
    RMDir "$INSTDIR"
SectionEnd

# Custom functions for the finish page
Function LaunchApplication
    # Check if kernel precompilation was selected
    ${If} ${MUI_FINISHPAGE_CHECKBOX_STATE} == ${BST_CHECKED}
        # Let the user know we're waiting for precompilation
        MessageBox MB_ICONINFORMATION|MB_OK "Ouija UI will launch after a short delay to allow kernel precompilation to begin. For best performance, allow the precompilation process to complete before using the application."
        
        # Wait a moment to allow kernel precompilation to start
        Sleep 2000
    ${EndIf}
    
    # Launch the application
    ExecShell "open" "$INSTDIR\Ouija-UI.exe"
FunctionEnd

Function RunKernelPrecompilation
    # Show message to inform user about kernel precompilation
    MessageBox MB_ICONINFORMATION|MB_OK "OpenCL kernel precompilation will run in a separate window.$\n$\nThis process may take a minute but will significantly improve application startup performance.$\n$\nPlease wait for the precompilation window to complete before using the application."
    
    DetailPrint "Starting OpenCL kernel precompilation..."
    SetDetailsPrint both
    
    # Check if GPU is available first
    ExecWait '"$INSTDIR\Ouija-CLI.exe" --list_devices' $0
    ${If} $0 != 0
        MessageBox MB_OK|MB_ICONEXCLAMATION "No OpenCL-compatible GPU was detected. Kernel precompilation may not be possible. You can try updating your graphics drivers and run precompilation later using the Start menu shortcut."
    ${Else}
        # Create a Start Menu shortcut for precompilation
        CreateShortCut "$SMPROGRAMS\${APP_NAME}\Precompile Kernels.lnk" "$INSTDIR\precompile_kernels.cmd"
        
        # Execute the precompilation script
        ExecShell "open" "$INSTDIR\precompile_kernels.cmd" "" SW_SHOW
        
        DetailPrint "Kernel precompilation started in a separate window."
        DetailPrint "The application will be ready to use when precompilation completes."
    ${EndIf}
    
    SetDetailsPrint none
FunctionEnd






























































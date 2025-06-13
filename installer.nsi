# Ouija NSIS Installer Script
# Requires NSIS (Nullsoft Scriptable Install System) to be installed

!define APP_NAME "Ouija"

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
!define MUI_FINISHPAGE_RUN_TEXT "Start ${APP_NAME}"
!define MUI_FINISHPAGE_RUN_NOTCHECKED

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
VIAddVersionKey "ProductVersion" "${APP_VERSION}.0"
VIAddVersionKey "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey "FileDescription" "Ouija - Balatro Seed Finder"
VIAddVersionKey "FileVersion" "${APP_VERSION}.0"
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
    File "/oname=precompile_kernels.ps1" "distribution\Ouija-v${APP_VERSION}-Windows\precompile_kernels.ps1"
    # Directories
    SetOutPath "$INSTDIR\lib"
    File /r "distribution\Ouija-v${APP_VERSION}-Windows\lib\*.*"
    SetOutPath "$INSTDIR\ouija_filters"
    File /r "distribution\Ouija-v${APP_VERSION}-Windows\ouija_filters\*.*"
    SetOutPath "$INSTDIR\ouija_configs"
    File /r "distribution\Ouija-v${APP_VERSION}-Windows\ouija_configs\*.*"
    
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
        MessageBox MB_OK|MB_ICONINFORMATION "Installation complete!$\n$\nGPU support detected. ${APP_NAME} is ready to use.$\n$\nKernels will be compiled automatically when needed."
    ${EndIf}
FunctionEnd

# Function RunAdvancedPrecompile has been replaced by RunKernelPrecompilation

# Uninstaller
Section "Uninstall"    # Remove files
    Delete "$INSTDIR\Ouija-UI.exe"
    Delete "$INSTDIR\Ouija-CLI.exe"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\LICENSE"
    Delete "$INSTDIR\Uninstall.exe"
    Delete "$INSTDIR\precompile_kernels.ps1"
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






























































































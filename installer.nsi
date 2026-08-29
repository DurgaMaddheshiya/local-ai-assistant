; Local AI Assistant NSIS Installer Script
; This creates a one-click installer for Windows

!include "MUI2.nsh"
!include "x64.nsh"
!include "nsDialogs.nsh"

; Basic settings
Name "Local AI Assistant"
OutFile "LocalAIAssistant-Setup.exe"
InstallDir "$PROGRAMFILES\LocalAIAssistant"
InstallDirRegKey HKLM "Software\LocalAIAssistant" "InstallLocation"

; Request admin rights
RequestExecutionLevel admin

; MUI Settings
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; Installer sections
Section "Install"
  SetOutPath "$INSTDIR"
  
  ; Copy application files
  File /r "dist\LocalAIAssistant\*.*"
  
  ; Copy frontend
  SetOutPath "$INSTDIR\frontend"
  File /r "frontend\*.*"
  
  ; Copy .env.example
  SetOutPath "$INSTDIR"
  File ".env.example"
  
  ; Create .env from example
  IfFileExists "$INSTDIR\.env" skipenv
  CopyFiles "$INSTDIR\.env.example" "$INSTDIR\.env"
  skipenv:
  
  ; Create data and logs directories
  CreateDirectory "$INSTDIR\data"
  CreateDirectory "$INSTDIR\logs"
  
  ; Create Start Menu shortcuts
  CreateDirectory "$SMPROGRAMS\Local AI Assistant"
  CreateShortCut "$SMPROGRAMS\Local AI Assistant\Local AI Assistant.lnk" "$INSTDIR\LocalAIAssistant.exe" "" "$INSTDIR\LocalAIAssistant.exe" 0
  CreateShortCut "$SMPROGRAMS\Local AI Assistant\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
  
  ; Create Desktop shortcut
  CreateShortCut "$DESKTOP\Local AI Assistant.lnk" "$INSTDIR\LocalAIAssistant.exe" "" "$INSTDIR\LocalAIAssistant.exe" 0
  
  ; Create Uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  ; Write registry keys
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LocalAIAssistant" "DisplayName" "Local AI Assistant"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LocalAIAssistant" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LocalAIAssistant" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LocalAIAssistant" "DisplayVersion" "1.0.0"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LocalAIAssistant" "Publisher" "Local AI"
  
  ; Registry key for InstallLocation
  WriteRegStr HKLM "Software\LocalAIAssistant" "InstallLocation" "$INSTDIR"
  
  ; Show completion message
  MessageBox MB_OK "Local AI Assistant installed successfully!$\n$\nBefore using, please:$\n1. Install Ollama from https://ollama.com/download$\n2. Run: ollama pull qwen2.5:3b$\n3. Run: ollama serve$\n4. Then launch Local AI Assistant"
SectionEnd

; Uninstaller
Section "Uninstall"
  ; Delete application files
  RMDir /r "$INSTDIR"
  
  ; Delete shortcuts
  Delete "$SMPROGRAMS\Local AI Assistant\Local AI Assistant.lnk"
  Delete "$SMPROGRAMS\Local AI Assistant\Uninstall.lnk"
  RMDir "$SMPROGRAMS\Local AI Assistant"
  Delete "$DESKTOP\Local AI Assistant.lnk"
  
  ; Delete registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LocalAIAssistant"
  DeleteRegKey HKLM "Software\LocalAIAssistant"
SectionEnd

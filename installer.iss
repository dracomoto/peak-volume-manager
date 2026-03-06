; ==========================================================================
; Peak Volume Manager - Inno Setup Installer Script
; ==========================================================================
;
; This script creates a professional Windows installer (.exe) from the
; PyInstaller output folder.
;
; Prerequisites:
;   1. Run the build script (build_installer.bat) first, which calls
;      PyInstaller to create dist/PeakVolumeManager/
;   2. Install Inno Setup 6 from https://jrsoftware.org/isinfo.php
;   3. Open this file in Inno Setup Compiler and click Build → Compile
;      OR run from command line:
;        iscc installer.iss
;
; Output: Output/PeakVolumeManager_Setup_1.0.0.exe
; ==========================================================================

#define MyAppName "Peak Volume Manager"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "PeakVolumeManager"
#define MyAppURL "https://github.com/yourusername/peak-volume-manager"
#define MyAppExeName "PeakVolumeManager.exe"

[Setup]
; Unique app ID — DO NOT change after first release (used for upgrades)
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Install location
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output installer
OutputDir=Output
OutputBaseFilename=PeakVolumeManager_Setup_{#MyAppVersion}

; Compression
Compression=lzma2/ultra64
SolidCompression=yes

; Appearance
WizardStyle=modern
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; Privileges — per-user install by default (no admin needed)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Misc
AllowNoIcons=yes
LicenseFile=
; Uncomment and point to a LICENSE.txt if you have one:
; LicenseFile=LICENSE.txt

; Minimum Windows version
MinVersion=10.0

; 64-bit only
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "autostart"; Description: "Start with Windows (run at login)"; GroupDescription: "Startup:"

[Files]
; Include the entire PyInstaller output folder
Source: "dist\PeakVolumeManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Include the icon separately for uninstall display
Source: "assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional task)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Registry]
; Auto-start with Windows (optional task)
; Uses HKCU so no admin rights needed
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
    ValueType: string; ValueName: "PeakVolumeManager"; \
    ValueData: """{app}\{#MyAppExeName}"""; \
    Flags: uninsdeletevalue; Tasks: autostart

[Run]
; Offer to launch after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up settings file on uninstall
Type: files; Name: "{app}\settings.json"
Type: dirifempty; Name: "{app}"

[Code]
// Kill the app before upgrading to avoid locked files
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssInstall then
  begin
    // Try to gracefully close the app if it's running
    Exec('taskkill', '/IM PeakVolumeManager.exe /F', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    Exec('taskkill', '/IM PeakVolumeManager.exe /F', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;

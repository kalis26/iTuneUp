#define MyAppName "iTuneUp"
#define MyAppVersion "1.3.1"
#define MyAppPublisher "Amine Mustapha Rachid"
#define MyAppExeName "iTuneUp.exe"
#define MyAppId "{{A9F92E1A-7E5B-4D2B-BF11-ITUNEUP127}}"
#define MyAppURL "https://github.com/kalis26/iTuneUp"
#define MyAppCopyright "Copyright (C) 2026 Amine Mustapha Rachid"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright={#MyAppCopyright}
VersionInfoVersion=1.3.1.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=iTuneUp - Apple Music-style Downloads
VersionInfoTextVersion={#MyAppVersion}
VersionInfoCopyright={#MyAppCopyright}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion=1.3.1.0
VersionInfoProductTextVersion={#MyAppVersion}
DefaultDirName={localappdata}\{#MyAppName}
PrivilegesRequired=lowest
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=iTuneUp-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=icon.ico
LicenseFile=LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional tasks"; Flags: unchecked

[Files]
; === Main application ===
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; === FFmpeg and FFprobe (installed alongside exe) ===
Source: "resources\ffmpeg.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "resources\ffprobe.exe"; DestDir: "{app}"; Flags: ignoreversion

; === Source code - Only specific folders and .py files ===
Source: "*.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "templates\*"; DestDir: "{app}\source\templates"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "static\*"; DestDir: "{app}\source\static"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "resources\*"; DestDir: "{app}\source\resources"; Excludes: "ffmpeg.exe,ffprobe.exe"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "library\*"; DestDir: "{app}\source\library"; Flags: recursesubdirs createallsubdirs ignoreversion skipifsourcedoesntexist
Source: "metadata\*"; DestDir: "{app}\source\metadata"; Flags: recursesubdirs createallsubdirs ignoreversion skipifsourcedoesntexist

; === Documentation ===
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch iTuneUp"; Flags: nowait postinstall skipifsilent

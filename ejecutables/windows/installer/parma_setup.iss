; ==============================================================================
; Parma — Script Oficial de Instalación Inno Setup para Windows
; ==============================================================================

#define MyAppName "Parma — Character Hub & Grimoire"
#define MyAppVersion "1.0.3"
#define MyAppPublisher "NMullerSM"
#define MyAppURL "https://github.com/NMullerSM/Parma-Character-hub-and-Grimore"
#define MyAppExeName "Parma.exe"

[Setup]
AppId={{D4E9F762-2C8B-419A-97BF-87D2E7C6912A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\Parma
DefaultGroupName=Parma
DisableProgramGroupPage=no
OutputBaseFilename=Parma-Setup-v{#MyAppVersion}
OutputDir=..\
SetupIconFile=..\..\..\parma.ico
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\Parma.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\portable\Parma\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\..\parma.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Parma"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\Parma.exe"
Name: "{group}\Desinstalar Parma"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Parma"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\Parma.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

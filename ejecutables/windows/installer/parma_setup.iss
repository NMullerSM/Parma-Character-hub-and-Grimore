; ==============================================================================
; Parma — Script Oficial de Instalación Inno Setup para Windows
; ==============================================================================

#define MyAppName "Parma — Character Hub & Grimoire"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "NMullerSM"
#define MyAppURL "https://github.com/NMullerSM/Dnd_Player_Dashboard"
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
UninstallDisplayIcon={app}\parma.ico
CreateUninstallRegKey=yes
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Empaquetar todo el directorio compilado por PyInstaller (onedir)
Source: "..\Parma\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Asegurar icono de alta resolución en la raíz para desinstalador y accesos directos
Source: "..\..\..\parma.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Parma"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar Parma"; Filename: "{uninstallexe}"; IconFilename: "{app}\parma.ico"
Name: "{autodesktop}\Parma"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,Parma}"; Flags: nowait postinstall skipifsilent

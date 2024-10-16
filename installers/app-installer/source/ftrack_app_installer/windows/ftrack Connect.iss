; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{33D139AD-52FD-4DB4-9D8D-6A66C389117A}
AppName=ftrack Connect
AppVersion=${VERSION}
;AppVerName=ftrack Connect 24.4.1
AppPublisher=ftrack AB
AppPublisherURL=https://www.ftrack.com/
AppSupportURL=https://www.ftrack.com/
AppUpdatesURL=https://www.ftrack.com/
DefaultDirName={pf}\ftrack Connect
DisableProgramGroupPage=yes
; Remove the following line to run in administrative install mode (install for all users.)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=${DIST_PATH}
OutputBaseFilename=ftrack_connect-${VERSION}-win64
SetupIconFile=${ROOT_PATH}\logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "${DIST_PATH}\ftrack Connect\ftrack Connect.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "${DIST_PATH}\ftrack Connect\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "${DIST_PATH}\ftrack Connect\tools\uv\uv.exe"; DestDir: "{app}\tools\uv"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\ftrack Connect"; Filename: "{app}\ftrack Connect.exe"
Name: "{autodesktop}\ftrack Connect"; Filename: "{app}\ftrack Connect.exe"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -Command ""irm https://astral.sh/uv/install.ps1 | iex"""; Flags: runhidden; StatusMsg: "Installing uv tool..."
Filename: "{app}\ftrack Connect.exe"; Description: "{cm:LaunchProgram,ftrack Connect}"; Flags: nowait postinstall skipifsilent



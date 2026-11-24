; Paths are resolved relative to this script file.
#define AppName "SonicControl"
#include "..\dist\soniccontrol_version.iss"
#define BundleName AppName + SonicControlVersion
#define DistDir "..\\dist\\" + BundleName
#define InstallerOutputDir "..\\dist\\SonicControlInstaller"

; Define your application
[Setup]
AppName={#BundleName}
AppVersion={#SonicControlVersion}
DefaultDirName={pf}\{#BundleName}
DefaultGroupName={#BundleName}
OutputDir={#InstallerOutputDir}
OutputBaseFilename={#AppName}{#SonicControlVersion}
Compression=lzma
SolidCompression=yes

; Create Dir for storing data and logging and set permissions
[Dirs]
Name: "{userappdata}\{#BundleName}"; Permissions: everyone-modify

; Include the files from the build directory
[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Define the icons to create
[Icons]
Name: "{group}\{#BundleName}"; Filename: "{app}\{#BundleName}.exe"; IconFilename: "{app}\soniccontrol_gui\resources\icons\usepat_logo_neu.ico"

; Define how to run the application after installation
[Run]
Filename: "{app}\{#BundleName}.exe"; Description: "{cm:LaunchProgram,{#BundleName}}"; Flags: nowait postinstall skipifsilent

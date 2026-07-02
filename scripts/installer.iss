; Paths are resolved relative to this script file.
#define AppName "SonicControl"
#define DistDir "..\\dist\\SonicControl"
#define InstallerOutputDir "..\\dist\\SonicControlInstaller"

; Define your application
[Setup]
AppName={#AppName}
AppVersion=1.0
DefaultDirName={pf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir={#InstallerOutputDir}
OutputBaseFilename=SonicControlInstaller
Compression=lzma
SolidCompression=yes

; Create Dir for storing data and logging and set permissions
[Dirs]
Name: "{userappdata}\{#AppName}"; Permissions: everyone-modify

; Include the files from the build directory
[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Define the icons to create
[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\SonicControl.exe"; IconFilename: "{app}\soniccontrol_gui\resources\icons\usepat_logo_neu.ico"

; Define how to run the application after installation
[Run]
Filename: "{app}\SonicControl.exe"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

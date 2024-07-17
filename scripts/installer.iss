; Define your application
[Setup]
AppName=SonicControl
AppVersion=1.0
DefaultDirName={pf}\SonicControl
DefaultGroupName=SonicControl
OutputDir=..\build\SonicControlInstaller
OutputBaseFilename=SonicControlInstaller
Compression=lzma
SolidCompression=yes

; Include the files from the build directory
[Files]
Source: "build\SonicControl\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Define the icons to create
[Icons]
Name: "{group}\SonicControl"; Filename: "{app}\SonicControl.exe"

; Define how to run the application after installation
[Run]
Filename: "{app}\SonicControl.exe"; Description: "{cm:LaunchProgram,SonicControl}"; Flags: nowait postinstall skipifsilent

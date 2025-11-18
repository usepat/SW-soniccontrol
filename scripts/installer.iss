; Define your application
[Setup]
AppName=SonicControl
AppVersion=1.0
DefaultDirName={pf}\SonicControl
DefaultGroupName=SonicControl
OutputDir=..\dist\SonicControlInstaller
OutputBaseFilename=SonicControlInstaller
Compression=lzma
SolidCompression=yes

; Create Dir for storing data and logging and set permissions
[Dirs]
Name: "{userappdata}\SonicControl"; Permissions: everyone-modify

; Include the files from the build directory
[Files]
Source: "..\dist\SonicControl\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Define the icons to create
[Icons]
Name: "{group}\SonicControl"; Filename: "{app}\SonicControl.exe"; IconFilename: "{app}\soniccontrol_gui\resources\icons\usepat_logo_neu.ico"

; Define how to run the application after installation
[Run]
Filename: "{app}\SonicControl.exe"; Description: "{cm:LaunchProgram,SonicControl}"; Flags: nowait postinstall skipifsilent

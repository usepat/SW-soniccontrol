; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "SonicControl"
#define MyAppVersion "1.9.3"
#define MyAppPublisher "usePAT, GmbH"
#define MyAppURL "https://www.usepat.com/"
#define MyAppExeName "SonicControl-1.9.4.exe"
#define MyAppAssocName MyAppName + ""
#define MyAppAssocExt ".myp"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{5498125E-C9B6-4B38-A817-BC18B59E13AA}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
ChangesAssociations=yes
DisableProgramGroupPage=yes
; Remove the following line to run in administrative install mode (install for all users.)
PrivilegesRequired=lowest
OutputDir=C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist
OutputBaseFilename=soniccontrol_setup
SetupIconFile=C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\src\soniccontrol\pictures\welle.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\_asyncio.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\_bz2.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\_ctypes.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\_decimal.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\_hashlib.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\_lzma.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\_multiprocessing.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\_overlapped.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\_queue.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\_socket.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\_ssl.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\_tkinter.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\_uuid.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-console-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-datetime-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-debug-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-errorhandling-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-file-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-file-l1-2-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-file-l2-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-handle-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-heap-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-interlocked-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-libraryloader-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-localization-l1-2-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-memory-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-namedpipe-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-processenvironment-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-processthreads-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-processthreads-l1-1-1.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-profile-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-rtlsupport-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-string-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-synch-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-synch-l1-2-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-sysinfo-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-timezone-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-core-util-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-crt-conio-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-crt-convert-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-crt-environment-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-crt-filesystem-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-crt-heap-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-crt-locale-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-crt-math-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-crt-private-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-crt-process-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-crt-runtime-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-crt-stdio-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-crt-string-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-crt-time-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\api-ms-win-crt-utility-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\base_library.zip"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\libcrypto-1_1.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\libffi-7.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\libopenblas64__v0.3.21-gcc_10_3_0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\libssl-1_1.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\MSVCP140.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\pyexpat.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\python39.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\select.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\tcl86t.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\tk86t.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\ucrtbase.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\unicodedata.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\VCRUNTIME140.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\VCRUNTIME140_1.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ilja Golovanov\Documents\dev\SonicControl_new\soniccontrol\dist\SonicControl-1.9.4\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Registry]
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocExt}\OpenWithProgids"; ValueType: string; ValueName: "{#MyAppAssocKey}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".myp"; ValueData: ""

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

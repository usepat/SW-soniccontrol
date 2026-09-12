@echo off
setlocal

echo create exe file with pyinstaller

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"

if defined PYTHON_EXE (
    set "_PYTHON_EXE=%PYTHON_EXE%"
) else (
    set "_PYTHON_EXE=%PROJECT_ROOT%\.venv\Scripts\python.exe"
)

if defined MAIN_SCRIPT (
    set "_MAIN_SCRIPT=%MAIN_SCRIPT%"
) else (
    set "_MAIN_SCRIPT=%PROJECT_ROOT%\src\soniccontrol_gui\build_main.py"
)

if defined SONIC_SCRIPT_EXAMPLES (
    set "_SONIC_SCRIPT_EXAMPLES=%SONIC_SCRIPT_EXAMPLES%"
) else (
    set "_SONIC_SCRIPT_EXAMPLES=%PROJECT_ROOT%\sonic_script_examples"
)

if defined DIST_DIR (
    set "_DIST_DIR=%DIST_DIR%"
) else (
    set "_DIST_DIR=%PROJECT_ROOT%\dist"
)

if defined WORK_DIR (
    set "_WORK_DIR=%WORK_DIR%"
) else (
    set "_WORK_DIR=%PROJECT_ROOT%\build\temp"
)

if defined SPEC_DIR (
    set "_SPEC_DIR=%SPEC_DIR%"
) else (
    set "_SPEC_DIR=%PROJECT_ROOT%\build\spec"
)

set "_ICON_ARG="
if defined ICON_FILE (
    if not exist "%ICON_FILE%" (
        echo Icon file not found at "%ICON_FILE%".
        exit /b 1
    )

    set "_ICON_ARG=--icon "%ICON_FILE%""
)

set "_VERSION_ARG="
if defined VERSION_FILE (
    if not exist "%VERSION_FILE%" (
        echo Version file not found at "%VERSION_FILE%".
        exit /b 1
    )

    set "_VERSION_ARG=--version-file "%VERSION_FILE%""
)

if not exist "%_PYTHON_EXE%" (
	echo Python from the project venv was not found at "%_PYTHON_EXE%".
	exit /b 1
)

if not exist "%_MAIN_SCRIPT%" (
	echo SonicControl entrypoint not found at "%_MAIN_SCRIPT%".
	exit /b 1
)

if not exist "%_SONIC_SCRIPT_EXAMPLES%" (
	echo sonic_script_examples not found at "%_SONIC_SCRIPT_EXAMPLES%".
	exit /b 1
)

if not exist "%_DIST_DIR%" mkdir "%_DIST_DIR%"
if not exist "%_WORK_DIR%" mkdir "%_WORK_DIR%"
if not exist "%_SPEC_DIR%" mkdir "%_SPEC_DIR%"

if /i "%~1"=="--dry-run" (
	echo PROJECT_ROOT=%PROJECT_ROOT%
	echo PYTHON_EXE=%_PYTHON_EXE%
	echo MAIN_SCRIPT=%_MAIN_SCRIPT%
	echo DIST_DIR=%_DIST_DIR%
	echo WORK_DIR=%_WORK_DIR%
	echo SPEC_DIR=%_SPEC_DIR%
	exit /b 0
)

set "EXTRA_PYINSTALLER_ARGS=%*"

"%_PYTHON_EXE%" -m PyInstaller --noconfirm --onedir --windowed ^
--name "SonicControl" ^
%_ICON_ARG% ^
%_VERSION_ARG% ^
--collect-all soniccontrol_gui ^
--collect-all soniccontrol ^
--collect-all sonic_protocol ^
--collect-all tkinter ^
--hidden-import=PIL._tkinter_finder ^
--hidden-import=PIL._imagingtk ^
--collect-all PIL ^
%EXTRA_PYINSTALLER_ARGS% ^
--add-data "%_SONIC_SCRIPT_EXAMPLES%;sonic_script_examples" ^
--distpath "%_DIST_DIR%" ^
--workpath "%_WORK_DIR%" ^
--specpath "%_SPEC_DIR%" ^
"%_MAIN_SCRIPT%"

exit /b %ERRORLEVEL%

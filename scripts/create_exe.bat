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

set "_CREATE_EXE_PY=%SCRIPT_DIR%create_exe.py"

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

if not exist "%_CREATE_EXE_PY%" (
    echo SonicControl packaging helper not found at "%_CREATE_EXE_PY%".
	exit /b 1
)

set "PYTHON_EXE=%_PYTHON_EXE%"
set "MAIN_SCRIPT=%_MAIN_SCRIPT%"
set "SONIC_SCRIPT_EXAMPLES=%_SONIC_SCRIPT_EXAMPLES%"
set "DIST_DIR=%_DIST_DIR%"
set "WORK_DIR=%_WORK_DIR%"
set "SPEC_DIR=%_SPEC_DIR%"
set "ICON_FILE="
set "VERSION_FILE="

if defined ICON_FILE set "ICON_FILE=%ICON_FILE%"
if defined VERSION_FILE set "VERSION_FILE=%VERSION_FILE%"

"%_PYTHON_EXE%" "%_CREATE_EXE_PY%" %*

exit /b %ERRORLEVEL%

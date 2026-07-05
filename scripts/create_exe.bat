@echo off
setlocal

echo create exe file with pyinstaller

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"

set "PYTHON_EXE=%PROJECT_ROOT%\.venv\Scripts\python.exe"
set "MAIN_SCRIPT=%PROJECT_ROOT%\src\soniccontrol_gui\build_main.py"
set "SONIC_SCRIPT_EXAMPLES=%PROJECT_ROOT%\sonic_script_examples"
set "DIST_DIR=%PROJECT_ROOT%\dist"
set "WORK_DIR=%PROJECT_ROOT%\build\temp"
set "SPEC_DIR=%PROJECT_ROOT%\build\spec"

if not exist "%PYTHON_EXE%" (
	echo Python from the project venv was not found at "%PYTHON_EXE%".
	exit /b 1
)

if not exist "%MAIN_SCRIPT%" (
	echo SonicControl entrypoint not found at "%MAIN_SCRIPT%".
	exit /b 1
)

if not exist "%SONIC_SCRIPT_EXAMPLES%" (
	echo sonic_script_examples not found at "%SONIC_SCRIPT_EXAMPLES%".
	exit /b 1
)

if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"
if not exist "%WORK_DIR%" mkdir "%WORK_DIR%"
if not exist "%SPEC_DIR%" mkdir "%SPEC_DIR%"

if not "%~1"=="" (
	if exist "%~1\src\soniccontrol_gui\__main__.py" shift
)

if /i "%~1"=="--dry-run" (
	echo PROJECT_ROOT=%PROJECT_ROOT%
	echo PYTHON_EXE=%PYTHON_EXE%
	echo MAIN_SCRIPT=%MAIN_SCRIPT%
	echo DIST_DIR=%DIST_DIR%
	echo WORK_DIR=%WORK_DIR%
	echo SPEC_DIR=%SPEC_DIR%
	exit /b 0
)

set "EXTRA_COLLECT_ARGS="

:loop
if "%~1"=="" goto :continue
set "EXTRA_COLLECT_ARGS=%EXTRA_COLLECT_ARGS% --collect-all %~1"
shift
goto :loop

:continue
"%PYTHON_EXE%" -m PyInstaller --noconfirm --onedir --windowed ^
--name "SonicControl" ^
--collect-all soniccontrol_gui ^
--collect-all soniccontrol ^
--collect-all sonic_protocol ^
--collect-all tkinter ^
--hidden-import=PIL._tkinter_finder ^
--hidden-import=PIL._imagingtk ^
--collect-all PIL ^
%EXTRA_COLLECT_ARGS% ^
--add-data "%SONIC_SCRIPT_EXAMPLES%;sonic_script_examples" ^
--distpath "%DIST_DIR%" ^
--workpath "%WORK_DIR%" ^
--specpath "%SPEC_DIR%" ^
"%MAIN_SCRIPT%"

exit /b %ERRORLEVEL%

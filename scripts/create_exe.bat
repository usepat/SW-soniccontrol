@echo off
set WORKSPACE_DIR=%1

echo "create exe file with pyinstaller"

:: Build the base PyInstaller command
set PYINSTALLER_CMD=PyInstaller --noconfirm --onedir --windowed ^
--name "SonicControl" ^
--collect-all soniccontrol_gui ^
--collect-all soniccontrol

:: Add additional --collect-all arguments for each parameter 
:: passed after the workspace directory
shift
:loop
if "%1"=="" goto :continue
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --collect-all %1
shift
goto :loop

:continue
:: Add the remaining arguments and execute
%PYINSTALLER_CMD% ^
--add-data "sonic_script_examples:sonic_script_examples" ^
"%WORKSPACE_DIR%\src\soniccontrol_gui\__main__.py"

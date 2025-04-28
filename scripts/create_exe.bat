@echo off
set WORKSPACE_DIR=%1

echo "create exe file with pyinstaller"

PyInstaller  --noconfirm --onedir --windowed ^
--name "SonicControl" ^
--collect-all soniccontrol_gui ^
--collect-all soniccontrol ^
--collect-all shared ^
".\src\soniccontrol_gui\__main__.py"

#!/bin/bash
WORKSPACE_DIR=$1

echo "create exe file with pyinstaller"

pyinstaller --noconfirm --onedir --windowed \
--name "SonicControl" \
--collect-all soniccontrol_gui \
--collect-all soniccontrol \
--add-data "sonic_script_examples:sonic_script_examples" \
"${WORKSPACE_DIR}/src/soniccontrol_gui/__main__.py"
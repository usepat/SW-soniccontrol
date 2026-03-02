#!/bin/bash
WORKSPACE_DIR=$1

echo "bundle application with pyinstaller"

pyinstaller --noconfirm --onedir --windowed \
--name "SonicControl" \
--collect-all soniccontrol_gui \
--collect-all soniccontrol \
--collect-all sonic_protocol \
--add-data "sonic_script_examples:sonic_script_examples" \
--distpath output/dist \
--workpath output/temp \
--specpath output/spec \
"${WORKSPACE_DIR}/src/soniccontrol_gui/__main__.py"

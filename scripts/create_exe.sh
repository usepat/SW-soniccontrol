#!/bin/bash
WORKSPACE_DIR=$1

# activate venv
source "$WORKSPACE_DIR/.venv/bin/activate"

echo "bundle application with pyinstaller"

# We need to add PIL as hidden import because it is dynamically loaded as plugin and else
# pyinstaller will not detect it

pyinstaller --noconfirm --onedir --windowed \
--name "SonicControl" \
--collect-all soniccontrol_gui \
--collect-all soniccontrol \
--collect-all sonic_protocol \
--collect-all tkinter \
--hidden-import=PIL._tkinter_finder \
--hidden-import=PIL._imagingtk \
--collect-all PIL \
--add-data "${WORKSPACE_DIR}/sonic_script_examples:sonic_script_examples" \
--distpath build/dist \
--workpath build/temp \
--specpath build/spec \
"${WORKSPACE_DIR}/src/soniccontrol_gui/__main__.py"

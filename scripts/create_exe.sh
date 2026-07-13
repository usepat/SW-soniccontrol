#!/bin/bash

# Deduce workspace directory from the script file path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$WORKSPACE_DIR/.venv/bin/activate"

# Collect all arguments passed to the script
EXTRA_ARGS=("$@")


echo "bundle application with pyinstaller"

# We need to add PIL as hidden import because it is dynamically loaded as plugin and else
# pyinstaller will not detect it

PYINSTALLER_ARGS=(
  --noconfirm --onedir --windowed \
  --name "SonicControl" \
  --collect-all soniccontrol_gui \
  --collect-all soniccontrol \
  --collect-all sonic_protocol \
  --collect-all tkinter \
  --hidden-import=PIL._tkinter_finder \
  --hidden-import=PIL._imagingtk \
  --collect-all PIL \
  --add-data "${WORKSPACE_DIR}/sonic_script_examples:sonic_script_examples" \
  --distpath "${WORKSPACE_DIR}/build/dist" \
  --workpath "${WORKSPACE_DIR}/build/temp" \
  --specpath "${WORKSPACE_DIR}/build/spec"
)

# Add all extra arguments to the PyInstaller command
PYINSTALLER_ARGS+=("${EXTRA_ARGS[@]}")
PYINSTALLER_ARGS+=("${WORKSPACE_DIR}/src/soniccontrol_gui/build_main.py")

echo "PyInstaller will be called with the following arguments:"
printf '%q ' "${PYINSTALLER_ARGS[@]}"
echo

# Execute the pyinstaller command
pyinstaller "${PYINSTALLER_ARGS[@]}"

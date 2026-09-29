#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_EXE="${PYTHON_EXE:-$WORKSPACE_DIR/.venv/bin/python}"
MAIN_SCRIPT="${MAIN_SCRIPT:-$WORKSPACE_DIR/src/soniccontrol_gui/build_main.py}"
SONIC_SCRIPT_EXAMPLES="${SONIC_SCRIPT_EXAMPLES:-$WORKSPACE_DIR/sonic_script_examples}"
DIST_DIR="${DIST_DIR:-$WORKSPACE_DIR/build/dist}"
WORK_DIR="${WORK_DIR:-$WORKSPACE_DIR/build/temp}"
SPEC_DIR="${SPEC_DIR:-$WORKSPACE_DIR/build/spec}"
ICON_FILE="${ICON_FILE:-}"
VERSION_FILE="${VERSION_FILE:-}"

if [[ ! -x "$PYTHON_EXE" ]]; then
  echo "Python executable not found at $PYTHON_EXE" >&2
  exit 1
fi

if [[ ! -f "$MAIN_SCRIPT" ]]; then
  echo "SonicControl entrypoint not found at $MAIN_SCRIPT" >&2
  exit 1
fi

if [[ ! -d "$SONIC_SCRIPT_EXAMPLES" ]]; then
  echo "sonic_script_examples not found at $SONIC_SCRIPT_EXAMPLES" >&2
  exit 1
fi

if [[ -n "$ICON_FILE" && ! -f "$ICON_FILE" ]]; then
  echo "Icon file not found at $ICON_FILE" >&2
  exit 1
fi

if [[ -n "$VERSION_FILE" && ! -f "$VERSION_FILE" ]]; then
  echo "Version file not found at $VERSION_FILE" >&2
  exit 1
fi

EXTRA_ARGS=("$@")

echo "bundle application with pyinstaller"

PYINSTALLER_ARGS=(
  --noconfirm --onedir --windowed
  --name "SonicControl"
  --collect-all soniccontrol_gui
  --collect-all soniccontrol
  --collect-all sonic_protocol
  --collect-all tkinter
  --hidden-import=PIL._tkinter_finder
  --hidden-import=PIL._imagingtk
  --collect-all PIL
  --add-data "$SONIC_SCRIPT_EXAMPLES:sonic_script_examples"
  --distpath "$DIST_DIR"
  --workpath "$WORK_DIR"
  --specpath "$SPEC_DIR"
)

if [[ -n "$ICON_FILE" ]]; then
  PYINSTALLER_ARGS+=(--icon "$ICON_FILE")
fi

if [[ -n "$VERSION_FILE" ]]; then
  PYINSTALLER_ARGS+=(--version-file "$VERSION_FILE")
fi

PYINSTALLER_ARGS+=("${EXTRA_ARGS[@]}" "$MAIN_SCRIPT")

echo "PyInstaller will be called with the following arguments:"
printf '%q ' "${PYINSTALLER_ARGS[@]}"
echo

"$PYTHON_EXE" -m PyInstaller "${PYINSTALLER_ARGS[@]}"

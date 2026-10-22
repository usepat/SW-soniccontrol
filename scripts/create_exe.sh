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
CREATE_EXE_PY="$SCRIPT_DIR/create_exe.py"

if [[ ! -x "$PYTHON_EXE" ]]; then
  echo "Python executable not found at $PYTHON_EXE" >&2
  exit 1
fi

if [[ ! -f "$CREATE_EXE_PY" ]]; then
  echo "SonicControl packaging helper not found at $CREATE_EXE_PY" >&2
  exit 1
fi

EXTRA_ARGS=("$@")

PYTHON_EXE="$PYTHON_EXE" \
MAIN_SCRIPT="$MAIN_SCRIPT" \
SONIC_SCRIPT_EXAMPLES="$SONIC_SCRIPT_EXAMPLES" \
DIST_DIR="$DIST_DIR" \
WORK_DIR="$WORK_DIR" \
SPEC_DIR="$SPEC_DIR" \
ICON_FILE="$ICON_FILE" \
VERSION_FILE="$VERSION_FILE" \
"$PYTHON_EXE" "$CREATE_EXE_PY" "${EXTRA_ARGS[@]}"

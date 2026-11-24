#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_EXE="${PYTHON_EXE:-$WORKSPACE_DIR/.venv/bin/python}"
SONIC_SCRIPT_EXAMPLES="${SONIC_SCRIPT_EXAMPLES:-$WORKSPACE_DIR/sonic_script_examples}"
DIST_DIR="${DIST_DIR:-$WORKSPACE_DIR/build/dist}"
WORK_DIR="${WORK_DIR:-$WORKSPACE_DIR/build/temp}"
SPEC_DIR="${SPEC_DIR:-$WORKSPACE_DIR/build/spec}"
ICON_FILE="${ICON_FILE:-}"
VERSION_FILE="${VERSION_FILE:-}"
CREATE_EXE_PY="$SCRIPT_DIR/create_exe.py"

if ! VERSION="$(git -C "$WORKSPACE_DIR" describe --tags --abbrev=0 --match 'v[0-9]*')"; then
  echo "No SonicControl version tag found. Fetch the SonicControl Git tags before building." >&2
  exit 1
fi
BUNDLE_NAME="SonicControl${VERSION}${SONICCONTROL_BUILD_SUFFIX:-}"
if [[ "${1:-}" == "--print-name" ]]; then
  printf '%s\n' "$BUNDLE_NAME"
  exit 0
fi

if [[ ! -x "$PYTHON_EXE" ]]; then
  echo "Python executable not found at $PYTHON_EXE" >&2
  exit 1
fi


MAIN_SCRIPT="${MAIN_SCRIPT:-$WORKSPACE_DIR/src/soniccontrol_gui/__main__.py}"

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

PYTHON_EXE="$PYTHON_EXE" \
MAIN_SCRIPT="$MAIN_SCRIPT" \
SONIC_SCRIPT_EXAMPLES="$SONIC_SCRIPT_EXAMPLES" \
DIST_DIR="$DIST_DIR" \
WORK_DIR="$WORK_DIR" \
SPEC_DIR="$SPEC_DIR" \
ICON_FILE="$ICON_FILE" \
VERSION_FILE="$VERSION_FILE" \
"$PYTHON_EXE" "$CREATE_EXE_PY" --name "$BUNDLE_NAME" "${EXTRA_ARGS[@]}"

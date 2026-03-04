#!/bin/bash

# Get the directory of the current script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define the project root relative to the script directory
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# set cwd to project root
cd $PROJECT_ROOT

# activate virtual environment
source .venv/bin/activate

# Define the plugins directory
PLUGINS_DIR="$FIRMWARE_BUILD_DIR_PATH/../tools/plugins"

# Check if the plugins directory exists
if [ ! -d "$PLUGINS_DIR" ]; then
  echo "Plugins directory does not exist: $PLUGINS_DIR"
  exit 1
fi

# Iterate through subdirectories of the plugins directory
for SUBDIR in "$PLUGINS_DIR"/*; do
  if [ -d "$SUBDIR" ] && [ -f "$SUBDIR/pyproject.toml" ]; then
    echo "Installing plugin from $SUBDIR"
    pip install -e "$SUBDIR"
  fi
done



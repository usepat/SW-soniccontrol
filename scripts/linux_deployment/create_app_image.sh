#!/bin/bash

# Get the directory of the current script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define the project root relative to the script directory
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Define the source and destination paths
SOURCE_DIR="$PROJECT_ROOT/linux_deployment/SonicControl.AppDir"
OUTPUT_DIR="$PROJECT_ROOT/output"

# Ensure the destination directory exists
mkdir -p "$OUTPUT_DIR"

# Copy the AppDir to the output directory
cp -r "$SOURCE_DIR" "$OUTPUT_DIR"

# create a standalone executable for the app
bash "$PROJECT_ROOT/create_exe.sh"

# copy the executable into the app dir folder
cp -r "$OUTPUT_DIR/dist/SonicControl/*"  "$OUTPUT_DIR/SonicControl.AppDir/usr/bin"

# create the final app image
# DEPENDENCY: you need to install appimagetool and add it to your $PATH
appimagetool "$OUTPUT_DIR/SonicControl.AppDir" "$OUTPUT_DIR/SonicControl.AppImage"

#!/bin/bash

# Get the directory of the current script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define the project root relative to the script directory
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# set cwd to project root
cd $PROJECT_ROOT

# activate virtual environment
source .venv/bin/activate

# Define destination paths
OUTPUT_DIR=./output
BUILD_DIR=./build
TOOLS_DIR="$FIRMWARE_BUILD_DIR_PATH/../tools"
FLASH_TOOLS_BIN_DIR="$TOOLS_DIR/plugins/flashing_tools/src/flashing_tools/linux-x64"

# Ensure the destination directory exists
mkdir -p "$OUTPUT_DIR"
mkdir -p "$BUILD_DIR"

# Copy the AppDir to the build directory
cp -r ./scripts/linux_deployment/SonicControl.AppDir "$BUILD_DIR"


# create a standalone executable for the app. Passing the current working directory
bash ./scripts/create_exe.sh \
    --collect-all configuration_gui \
    --collect-all flashing_tools \
    --collect-all usb_flashing \
    --collect-all uart_flashing \
    --copy-metadata configuration_gui \
    --copy-metadata flashing_tools \
    --copy-metadata usb_flashing \
    --copy-metadata uart_flashing \
    --hidden-import configuration_gui \
    --hidden-import flashing_tools \
    --hidden-import usb_flashing \
    --hidden-import uart_flashing \
    --paths "$TOOLS_DIR\plugins" \


# copy the executable into the app dir folder
cp -r "$BUILD_DIR/dist/SonicControl/"  "$BUILD_DIR/SonicControl.AppDir/usr/bin"

# Make App Run and Application executable
chmod +x "$BUILD_DIR/SonicControl.AppDir/AppRun" 
chmod +x "$BUILD_DIR/SonicControl.AppDir/usr/bin"

# create the final app image
./tools/appimagetool-x86_64.AppImage "$BUILD_DIR/SonicControl.AppDir" "$OUTPUT_DIR/SonicControl.AppImage"

# make the app image executable
chmod +x "$OUTPUT_DIR/SonicControl.AppImage" 

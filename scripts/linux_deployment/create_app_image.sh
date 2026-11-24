#!/bin/bash

set -euo pipefail

# Get the directory of the current script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define the project root relative to the script directory
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

OUTPUT_DIR="$PROJECT_ROOT/output"
BUILD_DIR="$PROJECT_ROOT/build"
APPDIR_TEMPLATE="$PROJECT_ROOT/scripts/linux_deployment/SonicControl.AppDir"
APPDIR_BUILD="$BUILD_DIR/SonicControl.AppDir"
DIST_DIR="${DIST_DIR:-$BUILD_DIR/dist}"
APPIMAGE_TOOL="$PROJECT_ROOT/tools/appimagetool-x86_64.AppImage"
CREATE_EXE="$PROJECT_ROOT/scripts/create_exe.sh"
BUNDLE_NAME="$(bash "$CREATE_EXE" --print-name)"
APPIMAGE="$OUTPUT_DIR/$BUNDLE_NAME.AppImage"

cd "$PROJECT_ROOT"

# activate virtual environment
source "$PROJECT_ROOT/.venv/bin/activate"

# Ensure the destination directory exists
mkdir -p "$OUTPUT_DIR"
mkdir -p "$BUILD_DIR"

# Recreate the AppDir in the build directory from the template
rm -rf "$APPDIR_BUILD"
cp -r "$APPDIR_TEMPLATE" "$APPDIR_BUILD"
mkdir -p "$APPDIR_BUILD/usr/bin"


# create a standalone executable for the app
DIST_DIR="$DIST_DIR" bash "$CREATE_EXE"

if [[ ! -f "$DIST_DIR/$BUNDLE_NAME/$BUNDLE_NAME" ]]; then
	echo "PyInstaller executable not found at $DIST_DIR/$BUNDLE_NAME/$BUNDLE_NAME" >&2
	exit 1
fi

# copy the executable into the app dir folder
cp -r "$DIST_DIR/$BUNDLE_NAME" "$APPDIR_BUILD/usr/bin/"
ln -s "$BUNDLE_NAME/$BUNDLE_NAME" "$APPDIR_BUILD/usr/bin/soniccontrol-launcher"

# Make App Run and Application executable
chmod +x "$APPDIR_BUILD/AppRun"
chmod +x "$APPDIR_BUILD/usr/bin/$BUNDLE_NAME/$BUNDLE_NAME"

if [[ ! -x "$APPIMAGE_TOOL" ]]; then
	echo "AppImageTool not found or not executable at $APPIMAGE_TOOL" >&2
	exit 1
fi

# create the final app image
ARCH=x86_64 "$APPIMAGE_TOOL" "$APPDIR_BUILD" "$APPIMAGE"

# make the app image executable
chmod +x "$APPIMAGE"

#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Installing PyInstaller if needed...${NC}"
pip install pyinstaller

# Set up environment variables for macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${YELLOW}Setting up macOS dependencies...${NC}"

    # Check if homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "Homebrew is not installed. Please install it first."
        exit 1
    fi

    # Install dependencies if not already installed
    echo -e "${YELLOW}Installing required libraries...${NC}"
    brew install gobject-introspection cairo pango gdk-pixbuf libffi

    # Set environment variables needed for the build
    export HOMEBREW_PREFIX="$(brew --prefix)"
    export DYLD_FALLBACK_LIBRARY_PATH="$HOMEBREW_PREFIX/lib"
    export PKG_CONFIG_PATH="$HOMEBREW_PREFIX/lib/pkgconfig"
    # Add GI_TYPELIB_PATH for PyGObject to find the typelib files
    export GI_TYPELIB_PATH="$HOMEBREW_PREFIX/lib/girepository-1.0"

    echo -e "${YELLOW}Using Homebrew prefix: ${HOMEBREW_PREFIX}${NC}"
fi

# Clean previous build if it exists
echo -e "${YELLOW}Cleaning previous build...${NC}"
rm -rf build dist

# Copy the runtime wrapper to the project root
echo -e "${YELLOW}Preparing runtime wrapper...${NC}"
chmod +x runtime_wrapper.sh

# Run PyInstaller with our spec file
echo -e "${YELLOW}Building with PyInstaller...${NC}"
pyinstaller resumecli.spec

# Copy the runtime wrapper to the distribution directory
echo -e "${YELLOW}Setting up runtime environment...${NC}"
cp runtime_wrapper.sh dist/resumecli/
chmod +x dist/resumecli/runtime_wrapper.sh

# Create a macOS-friendly launcher
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${YELLOW}Creating macOS launcher...${NC}"
    cat > dist/resumecli/resumecli.command << EOF
#!/bin/bash
# Launch resumecli with the correct environment
DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
"\$DIR/runtime_wrapper.sh" "\$@"
EOF
    chmod +x dist/resumecli/resumecli.command
fi

echo -e "${GREEN}Build complete!${NC}"
echo -e "${GREEN}The executable is in the dist/resumecli directory.${NC}"
echo -e "${GREEN}To run on macOS: ./dist/resumecli/resumecli.command${NC}"
echo -e "${GREEN}To run on any platform: ./dist/resumecli/runtime_wrapper.sh${NC}"

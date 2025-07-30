#!/usr/bin/env bash
set -e

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

    echo -e "${YELLOW}Using Homebrew prefix: ${HOMEBREW_PREFIX}${NC}"
fi

# Clean previous build if it exists
echo -e "${YELLOW}Cleaning previous build...${NC}"
rm -rf build dist

# Run PyInstaller with our spec file
echo -e "${YELLOW}Building with PyInstaller...${NC}"
pyinstaller resumecli.spec

echo -e "${GREEN}Build complete!${NC}"
echo -e "${GREEN}The executable is in the dist/resumecli directory.${NC}"

# Create a launcher script for macOS that sets the necessary environment variables
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${YELLOW}Creating macOS launcher script...${NC}"
    cat > dist/resumecli/run_resumecli.command << EOF
#!/bin/bash
# Set required environment variables for the bundled application
DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
export DYLD_FALLBACK_LIBRARY_PATH="\$DIR"
"\$DIR/resumecli" "\$@"
EOF
    chmod +x dist/resumecli/run_resumecli.command
    echo -e "${GREEN}Created launcher script: ./dist/resumecli/run_resumecli.command${NC}"
    echo -e "${GREEN}You can double-click run_resumecli.command to run the application${NC}"
fi

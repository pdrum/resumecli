#!/bin/bash
# resumecli for macOS

# Check for homebrew
if ! command -v brew &> /dev/null; then
    echo "Homebrew is not installed. Please install it from https://brew.sh"
    exit 1
fi

# Install dependencies
echo "Installing required dependencies..."
brew install gobject-introspection cairo pango gdk-pixbuf libffi

# Set environment variables
export HOMEBREW_PREFIX="$(brew --prefix)"
export DYLD_FALLBACK_LIBRARY_PATH="$HOMEBREW_PREFIX/lib"
export PKG_CONFIG_PATH="$HOMEBREW_PREFIX/lib/pkgconfig"
export GI_TYPELIB_PATH="$HOMEBREW_PREFIX/lib/girepository-1.0"

# Get the script directory
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find and execute the resumecli application
for EXECUTABLE_PATH in "$DIR/resumecli/resumecli.command" "$DIR/dist/resumecli/resumecli.command"; do
    if [ -f "$EXECUTABLE_PATH" ]; then
        "$EXECUTABLE_PATH" "$@"
        exit 0
    fi
done

# Error if executable not found
echo "Error: resumecli executable not found"
echo "Searched in:"
echo "  - $DIR/resumecli/resumecli.command"
echo "  - $DIR/dist/resumecli/resumecli.command"
echo "Current directory structure:"
find "$DIR" -type f -name "resumecli*" 2>/dev/null || echo "No resumecli files found"
exit 1

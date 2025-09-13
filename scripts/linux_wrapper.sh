#!/bin/bash
# resumecli for Linux

# Check for sudo
if ! command -v sudo &> /dev/null; then
    echo "This script requires 'sudo' to install dependencies."
    exit 1
fi

# Install dependencies
echo "Installing required dependencies..."
sudo apt-get update
sudo apt-get install -y \
  libgirepository1.0-dev \
  gobject-introspection \
  libcairo2-dev \
  libpango1.0-dev \
  libgdk-pixbuf2.0-dev \
  libffi-dev \
  shared-mime-info

# Set environment variables
export GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0"
export LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"

# Get the script directory
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find and execute the resumecli application
for EXECUTABLE_PATH in "$DIR/resumecli/resumecli.sh" "$DIR/dist/resumecli/resumecli.sh"; do
    if [ -f "$EXECUTABLE_PATH" ]; then
        "$EXECUTABLE_PATH" "$@"
        exit 0
    fi
done

# Error if executable not found
echo "Error: resumecli executable not found"
echo "Searched in:"
echo "  - $DIR/resumecli/resumecli.sh"
echo "  - $DIR/dist/resumecli/resumecli.sh"
echo "Current directory structure:"
find "$DIR" -type f -name "resumecli*" 2>/dev/null || echo "No resumecli files found"
exit 1

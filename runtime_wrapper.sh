#!/bin/bash
# This script sets up the environment for the bundled resumecli application

# Get the directory where this script is located
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set environment variables required for the GObject libraries
export GI_TYPELIB_PATH="$DIR/girepository-1.0"
export LD_LIBRARY_PATH="$DIR:$LD_LIBRARY_PATH"
export DYLD_LIBRARY_PATH="$DIR:$DYLD_LIBRARY_PATH"
export DYLD_FALLBACK_LIBRARY_PATH="$DIR:$DYLD_FALLBACK_LIBRARY_PATH"

# Run the application
exec "$DIR/resumecli" "$@"

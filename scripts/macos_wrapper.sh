#!/bin/bash
# resumecli installer for macOS

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

# Create installation directory in user's home
INSTALL_DIR="$HOME/.resumecli"
mkdir -p "$INSTALL_DIR"
echo "Installing resumecli to $INSTALL_DIR..."

# Find and copy the binary
for BINARY_PATH in "$DIR/resumecli/resumecli" "$DIR/dist/resumecli/resumecli" "$DIR/../build/resumecli/resumecli"; do
    if [ -f "$BINARY_PATH" ]; then
        echo "Found resumecli binary at $BINARY_PATH"

        # Copy the entire directory to maintain all dependencies
        PARENT_DIR=$(dirname "$BINARY_PATH")
        cp -R "$PARENT_DIR"/* "$INSTALL_DIR/"

        # Make the binary executable
        chmod +x "$INSTALL_DIR/resumecli"

        # Remove macOS quarantine attribute recursively from entire installation directory
        echo "Removing macOS quarantine attribute from all files in installation directory..."
        xattr -dr com.apple.quarantine "$INSTALL_DIR"

        # Create a wrapper script in the installation directory that always calls the installed binary
        cat > "$INSTALL_DIR/resumecli_wrapper" << EOF
#!/bin/bash
# Wrapper script for resumecli (hardcoded installation path)

# Set environment variables
export HOMEBREW_PREFIX="$(brew --prefix)"
export DYLD_FALLBACK_LIBRARY_PATH="$HOMEBREW_PREFIX/lib"
export PKG_CONFIG_PATH="$HOMEBREW_PREFIX/lib/pkgconfig"
export GI_TYPELIB_PATH="$HOMEBREW_PREFIX/lib/girepository-1.0"

# Run the resumecli binary
"$INSTALL_DIR/resumecli" "\$@"
EOF

        chmod +x "$INSTALL_DIR/resumecli_wrapper"

        break
    fi
done

### Symlink installation ###
# Install user-local command
SYMLINK_DIR="$HOME/.local/bin"
mkdir -p "$SYMLINK_DIR"
ln -sf "$INSTALL_DIR/resumecli_wrapper" "$SYMLINK_DIR/resumecli"
echo "Creating symlink in $SYMLINK_DIR..."

# Ensure the directory is in PATH
if [[ ":$PATH:" != *":$SYMLINK_DIR:"* ]]; then
    echo "Adding $SYMLINK_DIR to your PATH"
    echo "export PATH=\"$SYMLINK_DIR:\$PATH\"" >> "$HOME/.bash_profile"
    echo "export PATH=\"$SYMLINK_DIR:\$PATH\"" >> "$HOME/.zshrc" 2>/dev/null || true
fi

echo "✅ Installation successful!"
echo "You can now run 'resumecli' from anywhere in your terminal."

# If installed in a user-local directory, advise sourcing shell profile
if [[ "$SYMLINK_DIR" == "$HOME/.local/bin" || "$SYMLINK_DIR" == "$HOME/bin" ]]; then
    echo "To use resumecli in your current terminal session, run:"
    echo "  source ~/.bash_profile  # if you use bash"
    echo "  source ~/.zshrc         # if you use zsh"
fi

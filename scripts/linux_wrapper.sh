#!/usr/bin/env bash
# resumecli installer for Linux

# Check for package manager and install dependencies
if command -v apt-get &> /dev/null; then
    echo "Installing dependencies using apt..."
    sudo apt-get update
    sudo apt-get install -y \
      libgirepository1.0-dev \
      gobject-introspection \
      libcairo2-dev \
      libpango1.0-dev \
      libgdk-pixbuf2.0-dev \
      libffi-dev \
      shared-mime-info
elif command -v dnf &> /dev/null; then
    echo "Installing dependencies using dnf..."
    sudo dnf install -y \
      gobject-introspection-devel \
      cairo-devel \
      pango-devel \
      gdk-pixbuf2-devel \
      libffi-devel \
      shared-mime-info
elif command -v pacman &> /dev/null; then
    echo "Installing dependencies using pacman..."
    sudo pacman -Sy --noconfirm \
      gobject-introspection \
      cairo \
      pango \
      gdk-pixbuf2 \
      libffi \
      shared-mime-info
else
    echo "Warning: Could not detect package manager. You may need to install dependencies manually."
    echo "Required packages: gobject-introspection, cairo, pango, gdk-pixbuf2, libffi, shared-mime-info"
fi

# Set environment variables
export GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0"
export LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"

# Get the script directory
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create installation directory in user's home
INSTALL_DIR="$HOME/.resumecli"
mkdir -p "$INSTALL_DIR"
echo "Installing resumecli to $INSTALL_DIR..."

# Find and copy the binary
for BINARY_PATH in "$DIR/resumecli/resumecli" "$DIR/dist/resumecli/resumecli" "$DIR/../build/resumecli/resumecli"; do
    if [ -f "$BINARY_PATH" ] && file "$BINARY_PATH" | grep -q 'ELF'; then
        echo "Found Linux resumecli binary at $BINARY_PATH"

        # Copy the entire directory to maintain all dependencies
        PARENT_DIR=$(dirname "$BINARY_PATH")
        cp -R "$PARENT_DIR"/* "$INSTALL_DIR/"

        # Make the binary executable
        chmod +x "$INSTALL_DIR/resumecli"

        # Create a wrapper script in the installation directory with expanded install path
        cat > "$INSTALL_DIR/resumecli_wrapper" << EOF
#!/usr/bin/env bash
# Wrapper script for resumecli (hardcoded install path)

# Set environment variables
export GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0"
export LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:\$LD_LIBRARY_PATH"

# Run the resumecli binary from install dir
exec "$INSTALL_DIR/resumecli" "\$@"
EOF

        chmod +x "$INSTALL_DIR/resumecli_wrapper"

        break
    fi
done

### Symlink installation ###
SYMLINK_DIR="$HOME/.local/bin"
mkdir -p "$SYMLINK_DIR"
ln -sf "$INSTALL_DIR/resumecli_wrapper" "$SYMLINK_DIR/resumecli"
echo "Creating symlink in $SYMLINK_DIR..."

# Ensure the directory is in PATH across login and interactive shells
if [[ ":$PATH:" != *":$SYMLINK_DIR:"* ]]; then
    echo "Adding $SYMLINK_DIR to your PATH in your shell config files"
    for PROFILE in "$HOME/.bash_profile" "$HOME/.profile" "$HOME/.bashrc" "$HOME/.zshrc"; do
        if [ -f "$PROFILE" ]; then
            echo "export PATH=\"$SYMLINK_DIR:\$PATH\"" >> "$PROFILE"
        fi
    done
fi

echo "✅ Installation successful!"
echo "Open a new terminal session (or tab) to start using resumecli without additional steps."

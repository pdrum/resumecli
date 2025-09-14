#!/bin/bash
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
    if [ -f "$BINARY_PATH" ]; then
        echo "Found resumecli binary at $BINARY_PATH"

        # Copy the entire directory to maintain all dependencies
        PARENT_DIR=$(dirname "$BINARY_PATH")
        cp -R "$PARENT_DIR"/* "$INSTALL_DIR/"

        # Make the binary executable
        chmod +x "$INSTALL_DIR/resumecli"

        # Create a wrapper script in the installation directory (hardcoded install path)
        cat > "$INSTALL_DIR/resumecli_wrapper" << EOF
#!/bin/bash
# Wrapper script for resumecli (hardcoded install path)

# Set environment variables
export GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0"
export LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"

# Run the resumecli binary from install dir
"$INSTALL_DIR/resumecli" "\$@"
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

# Ensure the directory is in PATH
if [[ ":$PATH:" != *":$SYMLINK_DIR:"* ]]; then
    echo "Adding $SYMLINK_DIR to your PATH"
    echo 'export PATH="$SYMLINK_DIR:$PATH"' >> "$HOME/.bashrc"
    echo 'export PATH="$SYMLINK_DIR:$PATH"' >> "$HOME/.zshrc" 2>/dev/null || true
    echo 'export PATH="$SYMLINK_DIR:$PATH"' >> "$HOME/.profile" 2>/dev/null || true
    echo 'export PATH="$SYMLINK_DIR:$PATH"' >> "$HOME/.bash_profile" 2>/dev/null || true
fi

echo "✅ Installation successful!"
echo "You can now run 'resumecli' from anywhere in your terminal."

# Source the profile to update PATH in current session
if [ -f "$HOME/.bashrc" ]; then
    echo "To use resumecli in your current terminal session, run:"
    echo "  source ~/.bashrc"
fi

if [ -f "$HOME/.zshrc" ]; then
    echo "  source ~/.zshrc     # if you use zsh"
fi

# Provide instructions for login shells
if [ -f "$HOME/.profile" ]; then
    echo "  source ~/.profile  # for login/login shells"
fi

if [ -f "$HOME/.bash_profile" ]; then
    echo "  source ~/.bash_profile  # for login shells"
fi

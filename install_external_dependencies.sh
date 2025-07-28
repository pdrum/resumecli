#!/usr/bin/env bash

brew install gobject-introspection cairo pango gdk-pixbuf libffi
echo 'export HOMEBREW_PREFIX="$(brew --prefix)"' >> ~/.zshrc
echo 'export DYLD_FALLBACK_LIBRARY_PATH="$HOMEBREW_PREFIX/lib"' >> ~/.zshrc
echo 'export PKG_CONFIG_PATH="$HOMEBREW_PREFIX/lib/pkgconfig"' >> ~/.zshrc

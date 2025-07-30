#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Get the directory of the current working directory instead of __file__
script_dir = os.path.abspath(os.getcwd())

# Collect all necessary data files for weasyprint and other packages
datas = []
datas.extend(collect_data_files('weasyprint'))
datas.extend(collect_data_files('fonttools'))
datas.extend(collect_data_files('tinycss2'))
datas.extend(collect_data_files('jinja2'))
datas.extend(collect_data_files('jsonschema'))

# Collect template files
template_dir = os.path.join(script_dir, 'templates')
datas.append((template_dir, 'templates'))

# Collect schema file
datas.append((os.path.join(script_dir, 'cv.schema.json'), '.'))

# Hidden imports for weasyprint and other libraries
hidden_imports = []
hidden_imports.extend(collect_submodules('weasyprint'))
hidden_imports.extend(collect_submodules('fonttools'))
hidden_imports.extend(collect_submodules('cssselect2'))
hidden_imports.extend(collect_submodules('tinycss2'))
hidden_imports.extend(collect_submodules('jinja2'))
hidden_imports.extend(collect_submodules('jsonschema'))
hidden_imports.extend(['markdown', 'PIL'])

# Define binary dependencies based on the external dependencies script
# These are libraries that weasyprint depends on
binaries = []
if sys.platform == 'darwin':  # macOS
    homebrew_prefix = os.environ.get('HOMEBREW_PREFIX', '/opt/homebrew')
    lib_path = os.path.join(homebrew_prefix, 'lib')

    # Add GObject and related libraries
    for lib in [
        'libcairo.2.dylib',
        'libpango-1.0.0.dylib',
        'libpangocairo-1.0.0.dylib',
        'libgobject-2.0.0.dylib',
        'libglib-2.0.0.dylib',
        'libintl.8.dylib',
        'libffi.8.dylib',
        'libgdk_pixbuf-2.0.0.dylib',
    ]:
        lib_file = os.path.join(lib_path, lib)
        if os.path.exists(lib_file):
            binaries.append((lib_file, '.'))

a = Analysis(
    ['src/cli.py'],
    pathex=[script_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='resumecli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='resumecli',
)

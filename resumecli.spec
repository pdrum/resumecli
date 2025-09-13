#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import glob
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Get the directory of the current working directory
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

# Collect sample resume and schema files
datas.append((os.path.join(script_dir, 'cv.schema.json'), '.'))
datas.append((os.path.join(script_dir, 'cv.sample.yaml'), '.'))

# Hidden imports for weasyprint and other libraries
hidden_imports = []
hidden_imports.extend(collect_submodules('weasyprint'))
hidden_imports.extend(collect_submodules('fonttools'))
hidden_imports.extend(collect_submodules('cssselect2'))
hidden_imports.extend(collect_submodules('tinycss2'))
hidden_imports.extend(collect_submodules('jinja2'))
hidden_imports.extend(collect_submodules('jsonschema'))
hidden_imports.extend([
    'markdown',
    'PIL',
    'gi',
    'gi.repository.GLib',
    'gi.repository.GObject',
    'gi.repository.Gio',
    'gi.repository.Pango',
    'gi.repository.PangoCairo',
    'gi.repository.cairo'
])

# Define binary dependencies based on the external dependencies script
binaries = []
if sys.platform == 'darwin':  # macOS
    homebrew_prefix = os.environ.get('HOMEBREW_PREFIX', '/opt/homebrew')
    lib_path = os.path.join(homebrew_prefix, 'lib')

    # Libraries that need to be included
    lib_patterns = [
        'libgobject-2.0*.dylib',
        'libglib-2.0*.dylib',
        'libcairo*.dylib',
        'libpango*.dylib',
        'libharfbuzz*.dylib',
        'libfontconfig*.dylib',
        'libfreetype*.dylib',
        'libpixman*.dylib',
        'libffi*.dylib',
        'libgdk_pixbuf*.dylib',
        'libgio*.dylib',
        'libgmodule*.dylib',
        'libgthread*.dylib',
        'libintl*.dylib',
        'libiconv*.dylib'
    ]

    # Add all matching libraries
    for pattern in lib_patterns:
        for lib_file in glob.glob(os.path.join(lib_path, pattern)):
            if os.path.exists(lib_file):
                binaries.append((lib_file, '.'))

    # Include GI typelib files
    typelib_path = os.path.join(homebrew_prefix, 'lib', 'girepository-1.0')
    if os.path.exists(typelib_path):
        for typelib in glob.glob(os.path.join(typelib_path, '*.typelib')):
            binaries.append((typelib, 'girepository-1.0'))
elif sys.platform == 'linux':  # Linux
    # Libraries from /usr/lib/x86_64-linux-gnu
    lib_path = '/usr/lib/x86_64-linux-gnu'
    lib_patterns = [
        'libgobject-2.0.so*', 'libglib-2.0.so*', 'libcairo.so*',
        'libpango*.so*', 'libharfbuzz.so*', 'libfontconfig.so*',
        'libfreetype.so*', 'libpixman*.so*', 'libffi.so*',
        'libgdk_pixbuf-2.0.so*', 'libgio-2.0.so*', 'libgmodule-2.0.so*',
        'libgthread-2.0.so*', 'libintl.so*',
    ]

    # Add matching libraries
    for pattern in lib_patterns:
        for lib_file in glob.glob(os.path.join(lib_path, pattern)):
            if os.path.exists(lib_file):
                binaries.append((lib_file, '.'))

    # Include GI typelib files
    typelib_path = '/usr/lib/x86_64-linux-gnu/girepository-1.0'
    if os.path.exists(typelib_path):
        for typelib in glob.glob(os.path.join(typelib_path, '*.typelib')):
            binaries.append((typelib, 'girepository-1.0'))

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

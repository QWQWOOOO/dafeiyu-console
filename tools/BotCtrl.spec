# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['bot_ctl.py'],
    pathex=[],
    binaries=[],
    datas=[('release.json', '.')],
    hiddenimports=['pystray', 'PIL.Image', 'dashboard_view'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BotCtrl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['bot.ico'],
    version='version_info.txt',
)

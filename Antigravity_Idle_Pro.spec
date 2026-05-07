# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Admin\\Desktop\\SUPPER SPPED PC\\Antigravity_Idle\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\Admin\\Desktop\\SUPPER SPPED PC\\Antigravity_Idle\\gui', 'gui')],
    hiddenimports=['psutil', 'webview', 'GPUtil', 'wmi', 'winreg', 'clr'],
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
    name='Antigravity_Idle_Pro',
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
    version='C:\\Users\\Admin\\Desktop\\SUPPER SPPED PC\\Antigravity_Idle\\version_info.txt',
    uac_admin=True,
)

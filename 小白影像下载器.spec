# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('D:\\dengkaiyuan\\code\\GEHistoricalImagery-gui\\coord_convert.py', '.'), ('D:\\dengkaiyuan\\code\\GEHistoricalImagery-gui\\gdal', 'gdal'), ('D:\\dengkaiyuan\\code\\GEHistoricalImagery-gui\\resources', 'resources')]
binaries = [('D:\\dengkaiyuan\\code\\GEHistoricalImagery-gui\\GEHistoricalImagery.exe', '.')]
hiddenimports = ['coord_convert', 'folium', 'folium.plugins.draw', 'PyQt5.QtWebEngineWidgets']
tmp_ret = collect_all('folium')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('branca')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('jinja2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['D:\\dengkaiyuan\\code\\GEHistoricalImagery-gui\\map_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='小白影像下载器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['D:\\dengkaiyuan\\code\\GEHistoricalImagery-gui\\resources\\icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='小白影像下载器',
)

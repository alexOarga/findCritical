# -*- mode: python -*-

import sys
sys.setrecursionlimit(5000) # or more

block_cipher = None


a = Analysis(['../../main/GUI/run_GUI.py'],
             pathex=['../../main/GUI/', '../../main/core/'],
             binaries=[],
             datas=[('../../main/core/loading.gif', '.')],
             hiddenimports=['libsbml', 'PyQt5.sip', 'lzma', '_lzma' ,'backports.lzma'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='run_GUI',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='run_GUI')

# -*- mode: python -*-
a = Analysis(['advent.py'],
             hookspath=None,
             runtime_hooks=None)
a.datas += []
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='advent.exe',
          debug=False,
          strip=None,
          upx=False,
          console=False )

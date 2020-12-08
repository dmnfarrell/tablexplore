# -*- mode: python ; coding: utf-8 -*-
"""
    tablexplore spec file for pyinstaller.
    Created Nov 2020
    Copyright (C) Damien Farrell

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 3
    of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

block_cipher = None

a = Analysis(['main.py'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['tkinter','lib2to3','pywin.debugger', 'pywin.debugger.dbgcon'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False,
             datas=[ ('logo.png', 'pandasqtable/'),
		     ('pandasqtable/icons/*.png','pandasqtable/icons/'),
                     ('pandasqtable/datasets/*','pandasqtable/datasets/')  ])
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

#remove some files we don't need
exclude = ['Qt53D','Qt5Quick','Qt5Web','Qt5Multimedia',
 		       'sqlite3','d3dcompiler']

def remove_from_list(input, keys):
   outlist = []
   for item in input:
       name, _, _ = item
       flag = 0
       for key_word in keys:
           if name.find(key_word) > -1:
               flag = 1
       if flag != 1:
           outlist.append(item)
   return outlist

a.binaries = remove_from_list(a.binaries, exclude)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='tablexplore.exe',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          icon='img/logo.ico' )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='tablexplore')

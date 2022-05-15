#!/usr/bin/env python
"""
    Implements various widgets for tablexplore
    Created Oct 2021
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

from __future__ import absolute_import, division, print_function
import os, types, io
import string, copy
from collections import OrderedDict
import pandas as pd
import pylab as plt
from .qt import *
from . import util, core, plotting, dialogs

module_path = os.path.dirname(os.path.abspath(__file__))
iconpath = os.path.join(module_path, 'icons')

style = '''
    QLabel {
        font-size: 10px;
    }
    QWidget {
        max-width: 250px;
        min-width: 60px;
        font-size: 14px;
    }
    QPlainTextEdit {
        max-height: 80px;
    }
'''

class ScratchPad(QWidget):
    """Temporary storage widget for plots and other items.
    Currently supports storing text, mpl figures and dataframes"""
    def __init__(self, parent=None):
        super(ScratchPad, self).__init__(parent)
        self.parent = parent
        self.setMinimumSize(400,300)
        self.setGeometry(QtCore.QRect(300, 200, 800, 600))
        self.setWindowTitle("Scratchpad")
        self.createWidgets()
        sizepolicy = QSizePolicy()
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        #dict to store objects, these should be serialisable
        self.items = {}
        return

    def createWidgets(self):
        """Create widgets. Plot on left and dock for tools on right."""

        self.main = QTabWidget(self)
        self.main.setTabsClosable(True)
        self.main.tabCloseRequested.connect(lambda index: self.remove(index))
        layout = QVBoxLayout(self)
        toolbar = QToolBar("toolbar")
        layout.addWidget(toolbar)
        items = { 'new text':{'action':self.newText,'file':'document-new'},
                  'save': {'action':self.save,'file':'save'},
                  'save all': {'action':self.saveAll,'file':'save-all'},
                  'clear': {'action':self.clear,'file':'clear'}
                    }
        for i in items:
            if 'file' in items[i]:
                iconfile = os.path.join(iconpath,items[i]['file']+'.png')
                icon = QIcon(iconfile)
            else:
                icon = QIcon.fromTheme(items[i]['icon'])
            btn = QAction(icon, i, self)
            btn.triggered.connect(items[i]['action'])
            toolbar.addAction(btn)
        layout.addWidget(self.main)
        return

    def update(self, items):
        """Display a dict of stored objects"""

        self.main.clear()
        for name in items:
            obj = items[name]
            #print (name,type(obj))
            if type(obj) is str:
                te = dialogs.PlainTextEditor()
                te.setPlainText(obj)
                self.main.addTab(te, name)
            elif type(obj) is pd.DataFrame:
                tw = core.DataFrameTable(self.main, dataframe=obj)
                self.main.addTab(tw, name)
            else:
                pw = plotting.PlotWidget(self.main)
                self.main.addTab(pw, name)
                pw.figure = obj
                pw.draw()
                plt.tight_layout()
        self.items = items
        return

    def remove(self, idx):
        """Remove selected tab and item widget"""

        index = self.main.currentIndex()
        name = self.main.tabText(index)
        del self.items[name]
        self.main.removeTab(index)
        return

    def save(self):
        """Save selected item"""

        index = self.main.currentIndex()
        name = self.main.tabText(index)
        suff = "PNG files (*.png);;JPG files (*.jpg);;PDF files (*.pdf);;All files (*.*)"
        filename, _ = QFileDialog.getSaveFileName(self, "Save Figure", name, suff)
        if not filename:
            return

        fig = self.items[name]
        fig.savefig(filename+'.png', dpi=core.DPI)
        return

    def saveAll(self):
        """Save all figures in a folder"""

        dir =  QFileDialog.getExistingDirectory(self, "Save Folder",
                                             homepath, QFileDialog.ShowDirsOnly)
        if not dir:
            return
        for name in self.items:
            fig = self.items[name]
            fig.savefig(os.path.join(dir,name+'.png'), dpi=core.DPI)
        return

    def clear(self):
        """Clear plots"""

        self.items.clear()
        self.main.clear()
        return

    def newText(self):
        """Add a text editor"""

        name, ok = QInputDialog.getText(self, 'Name', 'Name:',
                    QLineEdit.Normal, '')
        if ok:
            tw = dialogs.PlainTextEditor()
            self.main.addTab(tw, name)
            self.items[name] = tw.toPlainText()
        return

    def closeEvent(self, event):
        """Close"""

        for idx in range(self.main.count()):
            name = self.main.tabText(idx)
            #print (name)
            w = self.main.widget(idx)
            #print (w)
            if type(w) == dialogs.PlainTextEditor:
                self.items[name] = w.toPlainText()
        return

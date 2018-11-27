#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
    Dataexplore2 table app
    Created May 2017
    Copyright (C) Damien Farrell

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 2
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
import sys,os,platform
from collections import OrderedDict
from PySide2 import QtCore
from PySide2.QtWidgets import *
from PySide2.QtGui import *
import pandas as pd
#from pandasqt.table import DragTable, DataTableWidget
from .core import TableModel, DataFrameTable
from .plotting import PlotViewer

class Application(QMainWindow):
    def __init__(self):

        QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("pandas qt example")
        self.setWindowIcon(QIcon('logo.png'))
        self.resize(880, 600)
        self.createMenu()
        self.main = QTabWidget(self)
        self.main.setGeometry(QtCore.QRect(20, 20, 825, 470))

        self.newProject()

        self.main.setFocus()
        self.setCentralWidget(self.main)
        self.statusBar().showMessage("Welcome", 3000)
        return

    def createMenu(self):

        self.file_menu = QMenu('&File', self)
        self.file_menu.addAction('&New', self.newProject,
                QtCore.Qt.CTRL + QtCore.Qt.Key_N)
        self.file_menu.addAction('&Quit', self.fileQuit,
                QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.sheet_menu = QMenu('&Sheet', self)
        self.menuBar().addMenu(self.sheet_menu)
        self.sheet_menu.addAction('&Add', self.addSheet)

        self.dataset_menu = QMenu('&Datasets', self)
        self.menuBar().addMenu(self.dataset_menu)
        self.dataset_menu.addAction('&Sample', self.sampleData)

        self.help_menu = QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)
        self.help_menu.addAction('&About', self.about)
        return

    def newProject(self):
        """New project"""

        self.main.clear()
        self.sheets = OrderedDict()
        self.addSheet()
        self.filename = None
        self.projopen = True
        return

    def closeProject(self):
        """Close"""

        return

    def addSheet(self, name=None):
        """Add a new sheet"""

        names = self.sheets.keys()
        if name is None:
            name = 'sheet'+str(len(self.sheets)+1)
        sheet = QSplitter(self.main)
        idx = self.main.addTab(sheet, name)
        self.sheets[idx] = sheet
        l = QHBoxLayout(sheet)
        t = DataFrameTable(sheet)
        t.setSortingEnabled(True)
        #t = DataTableWidget(self.sheet)
        l.addWidget(t)
        #pl = PlotViewer(sheet)
        #l.addWidget(pl)
        return

    def removeSheet(self, name):
        del self.sheets[name]
        return

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def sampleData(self):

        return

    def about(self):
        from . import __version__
        import matplotlib
        pandasver = pd.__version__
        pythonver = platform.python_version()
        mplver = matplotlib.__version__

        text='DataExplore2 Application\n'\
                +'Version '+__version__+'\n'\
                +'Copyright (C) Damien Farrell 2017-\n'\
                +'This program is free software; you can redistribute it and/or\n'\
                +'modify it under the terms of the GNU General Public License\n'\
                +'as published by the Free Software Foundation; either version 3\n'\
                +'of the License, or (at your option) any later version.\n'\
                +'Using Python v%s\n' %pythonver\
                +'pandas v%s, matplotlib v%s' %(pandasver,mplver)

        msg = QMessageBox.about(self, "About", text)
        return

if __name__ == '__main__':
    app = QApplication(sys.argv)

    aw = Application()
    aw.show()
    app.exec_()

#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Sample qt5 pandas table app
Damien Farrell 2016
"""

import sys,os
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QHBoxLayout, QSplitter
from PyQt5.QtWidgets import QMessageBox, QWidget, QTabWidget, QTableView, QSizePolicy
import pandas as pd
#from pandasqt.table import DragTable, DataTableWidget
from core import TableModel, DataFrameTable
from plotting import PlotViewer

class Application(QMainWindow):
    def __init__(self):

        QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("pandas qt example")
        self.resize(880, 600)
        self.createMenu()
        self.main = QTabWidget(self)
        self.main.setGeometry(QtCore.QRect(20, 20, 825, 470))

        self.sheets = {}
        self.addSheet()

        self.main.setFocus()
        self.setCentralWidget(self.main)
        self.statusBar().showMessage("Welcome", 3000)
        return

    def createMenu(self):

        self.file_menu = QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.sheet_menu = QMenu('&Sheet', self)
        self.menuBar().addMenu(self.sheet_menu)
        self.sheet_menu.addAction('&Add', self.addSheet)

        self.help_menu = QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)
        self.help_menu.addAction('&About', self.about)
        return

    def addSheet(self, name=None):

        sheet = self.sheets[0] = QSplitter(self.main)
        self.main.addTab(sheet, 'sheet1')
        l = QHBoxLayout(sheet)
        t = DataFrameTable(sheet)
        t.setSortingEnabled(True)
        #t = DataTableWidget(self.sheet)
        l.addWidget(t)

        pl = PlotViewer(sheet)
        l.addWidget(pl)
        return

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        from . import __version__
        pandasver = pd.__version__
        pythonver = platform.python_version()
        mplver = matplotlib.__version__

        text='DataExplore2 Application\n'\
                +'Version '+__version__+'\n'\
                +'Copyright (C) Damien Farrell 2014-\n'\
                +'This program is free software; you can redistribute it and/or\n'\
                +'modify it under the terms of the GNU General Public License\n'\
                +'as published by the Free Software Foundation; either version 3\n'\
                +'of the License, or (at your option) any later version.\n'\
                +'Using Python v%s\n' %pythonver\
                +'pandas v%s, matplotlib v%s' %(pandasver,mplver)

        QMessageBox.about(self, "About", text)
        return

if __name__ == '__main__':
    app = QApplication(sys.argv)

    aw = Application()
    aw.show()
    app.exec_()

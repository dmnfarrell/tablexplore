#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Sample qt5 pandas table app
Damien Farrell 2016
"""

import sys
import random
import matplotlib
matplotlib.use("Qt5Agg")
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QHBoxLayout, QSplitter
from PyQt5.QtWidgets import QMessageBox, QWidget, QTabWidget, QTableView, QSizePolicy
from numpy import arange, sin, pi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

#from pandasqt.table import DragTable, DataTableWidget
from core import TableModel, DataFrameTable

class PlotViewer():
    def __init__(self, parent=None):
        return


class MyMplCanvas(FigureCanvas):
    """Figure viewer"""

    def __init__(self, parent=None, width=6, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, facecolor='white')
        self.axes = fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        self.axes.hold(False)
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        return

class MyStaticMplCanvas(MyMplCanvas):
    """Simple canvas with a sine plot."""

    def compute_initial_figure(self):
        x = arange(0.0, 3.0, 0.05)
        y = [random.random()+i for i in x]
        self.axes.scatter(x, y, alpha=0.7)


class MyDynamicMplCanvas(MyMplCanvas):
    """A canvas that updates itself every second with a new plot."""

    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        timer.start(1000)
        return

    def compute_initial_figure(self):
        self.axes.plot([0, 1, 2, 3], [1, 2, 0, 4], 'r')

    def update_figure(self):
        # Build a list of 4 random integers between 0 and 10 (both inclusive)
        l = [random.randint(0, 10) for i in range(4)]
        self.axes.plot([0, 1, 2, 3], l, 'r')
        self.draw()
        return

class Application(QMainWindow):
    def __init__(self):

        QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")
        self.resize(635, 530)

        self.createMenu()
        self.main = QTabWidget(self)
        self.main.setGeometry(QtCore.QRect(5, 10, 625, 470))
        self.sheets = {}

        self.addSheet()

        self.main.setFocus()
        self.setCentralWidget(self.main)

        self.statusBar().showMessage("Hello", 2000)
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
        #t = QTableView(sheet, width=10, height=20)
        t = DataFrameTable(sheet)
        t.setSortingEnabled(True)

        #t = DataTableWidget(self.sheet)
        l.addWidget(t)

        sc = MyStaticMplCanvas(sheet, width=5, height=7, dpi=100)
        sc.compute_initial_figure()
        l.addWidget(sc)
        return

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QMessageBox.about(self, "About",
                    """ """  )

if __name__ == '__main__':
    app = QApplication(sys.argv)

    aw = Application()
    aw.setWindowTitle("PyQt5 Matplot Example")
    aw.show()
    #sys.exit(qApp.exec_())
    app.exec_()

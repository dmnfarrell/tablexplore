#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Sample qt5 pandas plotting module
Damien Farrell 2016
"""

import sys,os,random
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QMessageBox, QWidget, QTabWidget, QSizePolicy
from PyQt5.QtWidgets import QMenu, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QPushButton

class OptionsWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent, height=10)
        self.label = QLabel('Some Text')
        vbox = QVBoxLayout(self)
        okbutton = QPushButton("plot")
        okbutton.clicked.connect(self.update)
        vbox.addWidget(okbutton)
        self.setLayout(vbox)
        self.parent = parent
        return

    def update(self):
        self.parent.plot()
        return

class PlotViewer(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.createWidgets()
        return

    def createWidgets(self):
        #frame = QSplitter(self)

        vbox = QVBoxLayout(self)
        #vbox.addStretch(1)
        sc = self.sc = MyMplCanvas(self, width=5, height=7, dpi=100)
        sc.compute_figure()
        vbox.addWidget(sc)
        ow = OptionsWidget(self)
        vbox.addWidget(ow)
        return

    def plot(self):
        self.sc.compute_figure()
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

    def compute_figure(self):
        import numpy as np
        x = np.arange(0.0, 3.0, 0.05)
        y = [random.random()+i for i in x]
        self.axes.scatter(x, y, alpha=0.7)
        self.draw()
        return

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
        l = [random.randint(0, 10) for i in range(4)]
        self.axes.plot([0, 1, 2, 3], l, 'r')
        self.draw()
        return

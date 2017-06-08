#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    Sample dataexplore2 plotting module
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
import sys,os,random
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pylab as plt
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QMessageBox, QWidget, QTabWidget, QSizePolicy
from PyQt5.QtWidgets import QMenu, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore

colormaps = sorted(m for m in plt.cm.datad if not m.endswith("_r"))

class OptionsWidget(QWidget):
    def __init__(self, parent):

        super(QWidget, self).__init__(parent, height=10)
        self.parent = parent
        self.label = QLabel('Some Text')
        vbox = QHBoxLayout(self)
        button = QPushButton("plot")
        icon = QIcon.fromTheme("insert-image")
        button.setIcon(QIcon(icon))
        button.setIconSize(QtCore.QSize(24,24))
        button.clicked.connect(self.parent.plot)
        vbox.addWidget(button)
        button = QPushButton("apply")
        button.clicked.connect(self.applyOptions)
        vbox.addWidget(button)
        button = QPushButton("clear")
        button.clicked.connect(self.parent.clear)
        vbox.addWidget(button)
        self.setLayout(vbox)
        return

    def applyOptions(self):

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
        sc = self.sc = MplCanvas(self, width=5, height=7, dpi=100)
        self.plot()
        vbox.addWidget(sc)
        ow = OptionsWidget(self)
        vbox.addWidget(ow)
        return

    def plot(self):
        self.sc.sample_figure()
        return

    def clear(self):
        self.sc.axes.clear()
        return

class MplCanvas(FigureCanvas):
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

    def sample_figure(self):

        x = np.arange(0.0, 3.0, 0.05)
        y = [random.random()+i for i in x]
        self.axes.scatter(x, y, alpha=0.7)
        self.draw()
        return

class DynamicMplCanvas(MplCanvas):
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

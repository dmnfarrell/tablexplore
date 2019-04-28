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
#import matplotlib
#matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
#import pylab as plt
import numpy as np
import pandas as pd
from PySide2 import QtCore
from PySide2.QtWidgets import *
from PySide2.QtGui import *

#colormaps = sorted(m for m in plt.cm.datad if not m.endswith("_r"))

class OptionsWidget(QWidget):
    def __init__(self, parent):

        super(OptionsWidget, self).__init__(parent)
        self.parent = parent
        self.label = QLabel('Some Text')

        hbox = QHBoxLayout(self)
        w = QLabel('ssss')
        hbox.addWidget(w)
        w = QSpinBox()
        w.setRange(0,10)
        #w.setLabel('sss')
        hbox.addWidget(w)

        #self.setLayout(hbox)
        return

    def applyOptions(self):

        return

    def update(self):
        self.parent.plot()
        return

class PlotViewer(QWidget):
    def __init__(self, parent=None):
        super(PlotViewer, self).__init__(parent)

        self.createWidgets()
        return

    def createWidgets(self):

        self.main = QSplitter(self)
        vbox = QVBoxLayout()
        #self.main = QWidget(self)
        #l = QVBoxLayout(self.main)

        sc = self.canvas = MyMplCanvas(self.main, width=8, height=10, dpi=100)
        #l.addWidget(sc)
        vbox.addWidget(sc)
        bw = self.createButtons(self)
        vbox.addWidget(bw)
        ow = OptionsWidget(self)
        vbox.addWidget(ow)
        self.setLayout(vbox)
        self.plot()
        return

    def createButtons(self, parent):
        bw = self.button_widget = QWidget(parent)
        vbox = QHBoxLayout(bw)
        button = QPushButton("plot")
        icon = QIcon.fromTheme("insert-image")
        button.setIcon(QIcon(icon))
        button.setIconSize(QtCore.QSize(24,24))
        button.clicked.connect(self.plot)
        vbox.addWidget(button)
        #button = QPushButton("apply")
        #button.clicked.connect(self.applyOptions)
        #vbox.addWidget(button)
        button = QPushButton("clear")
        button.clicked.connect(self.clear)
        vbox.addWidget(button)
        return bw

    def plot(self):
        self.canvas.sample_figure()
        return

    def clear(self):
        self.canvas.axes.clear()
        self.canvas.draw()
        return

class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        self.compute_initial_figure()

        FigureCanvas.__init__(self, fig)
        #self.setParent(parent)
        #FigureCanvas.setSizePolicy(self,
        #                           QtWidgets.QSizePolicy.Expanding,
        #                           QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


    def plot(self):
        data = [random.random() for i in range(25)]
        ax = self.figure.add_subplot(111)
        ax.plot(data, 'r-')
        ax.set_title('PyQt Matplotlib Example')
        self.draw()

    def sample_figure(self):

        x = np.arange(0.0, 3.0, 0.05)
        y = [random.random()+i for i in x]
        self.axes.scatter(x, y, alpha=0.7)
        self.draw()
        return

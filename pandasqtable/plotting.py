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
from collections import OrderedDict
#import matplotlib
#matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
import pylab as plt
import numpy as np
import pandas as pd
from PySide2 import QtCore
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from .dialogs import *

colormaps = sorted(m for m in plt.cm.datad if not m.endswith("_r"))
markers = ['','o','.','^','v','>','<','s','+','x','p','d','h','*']
linestyles = ['-','--','-.',':','steps']

class OptionsWidget(QTabWidget):
    def __init__(self, parent):

        super(OptionsWidget, self).__init__(parent)
        self.parent = parent
        self.setGeometry(QtCore.QRect(20, 20, 600, 600))
        w = QWidget(self)
        idx = self.addTab(w, 'base')
        baseopts = MPLBaseOptions(parent=self)
        dialog = baseopts.showDialog(w)
        dialog.resize(200,200)
        l=QVBoxLayout(w)
        l.addWidget(dialog)
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

        sc = self.canvas = MyMplCanvas(self, width=8, height=10, dpi=100)
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
        icon = QIcon.fromTheme("applications-graphics")
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
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        return

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

class BaseOptions(object):
    """Class to generate widget dialog for dict of options"""
    def __init__(self, parent=None):
        """Setup variables"""

        self.parent = parent
        #df = self.parent.table.model.df
        return

    def applyOptions(self):
        """Set the plot kwd arguments from the tk variables"""

        kwds = {}
        for i in self.opts:
            pass
        self.kwds = kwds
        return

    def apply(self):
        self.applyOptions()
        if self.callback != None:
            self.callback()
        return

    def showDialog(self, parent, layout='horizontal'):
        """Auto create tk vars, widgets for corresponding options and
           and return the frame"""

        dialog = dialogFromOptions(parent, self.opts, self.groups,
                                        layout=layout)
        return dialog


class MPLBaseOptions(BaseOptions):
    """Class to provide a dialog for matplotlib options and returning
        the selected prefs"""

    kinds = ['line', 'scatter', 'bar', 'barh', 'pie', 'histogram', 'boxplot', 'violinplot', 'dotplot',
             'heatmap', 'area', 'hexbin', 'contour', 'imshow', 'scatter_matrix', 'density', 'radviz', 'venn']
    legendlocs = ['best','upper right','upper left','lower left','lower right','right','center left',
                'center right','lower center','upper center','center']
    defaultfont = 'monospace'

    def __init__(self, parent=None):
        """Setup variables"""

        self.parent = parent
        '''if self.parent is not None:
            df = self.parent.table.model.df
            datacols = list(df.columns)
            datacols.insert(0,'')
        else:
            datacols=[]'''
        datacols=[]
        scales = ['linear','log']
        grps = {'data':['by','by2','labelcol','pointsizes'],
                'formats':['font','marker','linestyle','alpha'],
                'sizes':['fontsize','ms','linewidth'],
                'general':['kind','bins','stacked','subplots','use_index','errorbars'],
                'axes':['grid','legend','showxlabels','showylabels','sharex','sharey','logx','logy'],
                'colors':['colormap','bw','clrcol','cscale','colorbar']}
        order = ['general','data','axes','sizes','formats','colors']
        self.groups = OrderedDict((key, grps[key]) for key in order)
        opts = self.opts = {'font':{'type':'font','default':self.defaultfont},
                'fontsize':{'type':'scale','default':12,'range':(5,40),'interval':1,'label':'font size'},
                'marker':{'type':'combobox','default':'','items': markers},
                'linestyle':{'type':'combobox','default':'-','items': linestyles},
                'ms':{'type':'scale','default':5,'range':(1,80),'interval':1,'label':'marker size'},
                'grid':{'type':'checkbutton','default':0,'label':'show grid'},
                'logx':{'type':'checkbutton','default':0,'label':'log x'},
                'logy':{'type':'checkbutton','default':0,'label':'log y'},
                #'rot':{'type':'entry','default':0, 'label':'xlabel angle'},
                'use_index':{'type':'checkbutton','default':1,'label':'use index'},
                'errorbars':{'type':'checkbutton','default':0,'label':'errorbar column'},
                'clrcol':{'type':'combobox','items':datacols,'label':'color by value','default':''},
                'cscale':{'type':'combobox','items':scales,'label':'color scale','default':'linear'},
                'colorbar':{'type':'checkbutton','default':0,'label':'show colorbar'},
                'bw':{'type':'checkbutton','default':0,'label':'black & white'},
                'showxlabels':{'type':'checkbutton','default':1,'label':'x tick labels'},
                'showylabels':{'type':'checkbutton','default':1,'label':'y tick labels'},
                'sharex':{'type':'checkbutton','default':0,'label':'share x'},
                'sharey':{'type':'checkbutton','default':0,'label':'share y'},
                'legend':{'type':'checkbutton','default':1,'label':'legend'},
                #'loc':{'type':'combobox','default':'best','items':self.legendlocs,'label':'legend loc'},
                'kind':{'type':'combobox','default':'line','items':self.kinds,'label':'plot type'},
                'stacked':{'type':'checkbutton','default':0,'label':'stacked'},
                'linewidth':{'type':'scale','default':1.5,'range':(0,10),'interval':0.1,'label':'line width'},
                'alpha':{'type':'scale','default':0.9,'range':(0,1),'interval':0.1,'label':'alpha'},
                'subplots':{'type':'checkbutton','default':0,'label':'multiple subplots'},
                'colormap':{'type':'combobox','default':'Spectral','items':colormaps},
                'bins':{'type':'entry','default':20,'width':10},
                'by':{'type':'combobox','items':datacols,'label':'group by','default':''},
                'by2':{'type':'combobox','items':datacols,'label':'group by 2','default':''},
                'labelcol':{'type':'combobox','items':datacols,'label':'point labels','default':''},
                'pointsizes':{'type':'combobox','items':datacols,'label':'point sizes','default':''},
                }
        self.kwds = {}
        return

    def applyOptions(self):
        """Set the plot kwd arguments from the tk variables"""

        BaseOptions.applyOptions(self)
        size = self.kwds['fontsize']
        plt.rc("font", family=self.kwds['font'], size=size)
        plt.rc('legend', fontsize=size-1)
        return

    def update(self, df):
        """Update data widget(s) when dataframe changes"""

        if util.check_multiindex(df.columns) == 1:
            cols = list(df.columns.get_level_values(0))
        else:
            cols = list(df.columns)
        #add empty value
        cols = ['']+cols
        self.widgets['by']['values'] = cols
        self.widgets['by2']['values'] = cols
        self.widgets['labelcol']['values'] = cols
        self.widgets['clrcol']['values'] = cols
        return

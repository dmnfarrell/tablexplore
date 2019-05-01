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


class PlotViewer(QWidget):
    """Plot viewer class"""
    def __init__(self, table, parent=None):
        super(PlotViewer, self).__init__(parent)
        self.parent = parent
        self.table = table
        self.createWidgets()
        self.currentdir = os.path.expanduser('~')
        return

    def createWidgets(self):

        self.main = QSplitter(self)
        vbox = QVBoxLayout()

        #sc = self.canvas = MyMplCanvas(self, width=8, height=10, dpi=100)
        #l.addWidget(sc)
        self.fig, self.canvas = addFigure(self)
        self.ax = self.fig.add_subplot(111)
        vbox.addWidget(self.canvas)
        bw = self.createButtons(self)
        vbox.addWidget(bw)
        #ow = OptionsWidget(self)
        ow = self.createDialogs()
        vbox.addWidget(ow)
        self.setLayout(vbox)
        self.plot()
        return

    def createDialogs(self):
        tab = QTabWidget(self)
        w = QWidget(tab)
        idx = tab.addTab(w, 'base')
        self.baseopts = MPLBaseOptions(parent=self)
        dialog = self.baseopts.showDialog(w)
        dialog.resize(200,200)
        l=QVBoxLayout(w)
        l.addWidget(dialog)
        return tab

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

    def simple_plot(self, df):
        """test plot"""

        kwds = self.baseopts.kwds
        self.ax = self.fig.add_subplot(111)
        cols=df.columns
        x=df[cols[0]]
        y=df[cols[1]]
        cmap = plt.cm.get_cmap(kwds['colormap'])
        self.ax.scatter(x, y, s=kwds['ms']*10, marker=kwds['marker'] )
        self.canvas.draw()
        return

    def plot(self):
        self.replot()
        return

    def clear(self):
        self.canvas.axes.clear()
        self.canvas.draw()
        return

    def replot(self, data=None):

        self.clear()
        self.baseopts.applyOptions()
        if data is None:
            self.data = self.table.getSelectedDataFrame()
        else:
            self.data = data
        self.simple_plot(self.data)
        #self.updateStyle()
        #self.applyPlotoptions()
        #self.plotCurrent()
        return

    def plotCurrent(self, redraw=True):
        """Plot the current data"""

        #layout = self.globalopts['grid layout']
        #gridmode = self.layoutopts.modevar.get()
        #plot3d = self.globalopts['3D plot']
        self._initFigure()
        if layout == 1 and gridmode == 'multiviews':
            self.plotMultiViews()
        elif layout == 1 and gridmode == 'splitdata':
            self.plotSplitData()
        elif plot3d == 1:
            self.plot3D(redraw=redraw)
        else:
            self.plot2D(redraw=redraw)
        return

    def clear(self):
        """Clear plot"""

        self.fig.clear()
        self.ax = None
        self.canvas.draw()
        self.table.plotted=None
        self.gridaxes = {}
        return

    def _initFigure(self):
        """Clear figure or add a new axis to existing layout"""

        from matplotlib.gridspec import GridSpec
        layout = self.globalopts['grid layout']
        plot3d = self.globalopts['3D plot']

        #plot layout should be tracked by plotlayoutoptions
        gl = self.layoutopts

        if plot3d == 1:
            proj = '3d'
        else:
            proj = None
        if layout == 0:
            #default layout is just a single axis
            self.fig.clear()
            self.gridaxes={}
            self.ax = self.fig.add_subplot(111, projection=proj)
        else:
            #get grid layout from layout opt
            rows = gl.rows
            cols = gl.cols
            x = gl.selectedrows
            y = gl.selectedcols
            r=min(x); c=min(y)
            rowspan = gl.rowspan
            colspan = gl.colspan
            top = .92
            bottom = .1
            #print (rows,cols,r,c)
            #print (rowspan,colspan)

            ws = cols/10-.05
            hs = rows/10-.05
            gs = self.gridspec = GridSpec(rows,cols,top=top,bottom=bottom,
                                          left=0.1,right=0.9,wspace=ws,hspace=hs)
            name = str(r+1)+','+str(c+1)
            if name in self.gridaxes:
                ax = self.gridaxes[name]
                if ax in self.fig.axes:
                    self.fig.delaxes(ax)
            self.ax = self.fig.add_subplot(gs[r:r+rowspan,c:c+colspan], projection=proj)
            self.gridaxes[name] = self.ax
            #update the axes widget
            self.layoutopts.updateAxesList()
        return

def addFigure(parent, figure=None, resize_callback=None):
    """Create a tk figure and canvas in the parent frame"""

    if figure == None:
        figure = Figure(figsize=(5,4), dpi=80, facecolor='white')

    canvas = FigureCanvas(figure)
    canvas.updateGeometry()
    return figure, canvas

class BaseOptions(object):
    """Class to generate widget dialog for dict of options"""
    def __init__(self, parent=None):
        """Setup variables"""

        self.parent = parent
        #df = self.parent.table.model.df
        return

    def applyOptions(self):
        """Set the plot kwd arguments from the widgets"""

        kwds = {}
        for i in self.opts:
            val = None
            if i in self.widgets:
                w = self.widgets[i]
                if type(w) is QLineEdit:
                    val = w.text()
                elif type(w) is QComboBox:
                    val = w.currentText()
                elif type(w) is QCheckBox:
                    val = w.isChecked()
                elif type(w) is QSlider:
                    val = w.value()
                if val != None:
                    kwds[i] = val
                print (val, i)
        self.kwds = kwds
        #print (self.kwds)
        return

    def apply(self):
        self.applyOptions()
        if self.callback != None:
            self.callback()
        return

    def showDialog(self, parent, layout='horizontal'):
        """Auto create tk vars, widgets for corresponding options and
           and return the frame"""

        dialog, self.widgets = dialogFromOptions(parent, self.opts, self.groups,
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
                'fontsize':{'type':'slider','default':12,'range':(5,40),'interval':1,'label':'font size'},
                'marker':{'type':'combobox','default':'','items': markers},
                'linestyle':{'type':'combobox','default':'-','items': linestyles},
                'ms':{'type':'slider','default':5,'range':(1,80),'interval':1,'label':'marker size'},
                'grid':{'type':'checkbox','default':0,'label':'show grid'},
                'logx':{'type':'checkbox','default':0,'label':'log x'},
                'logy':{'type':'checkbox','default':0,'label':'log y'},
                #'rot':{'type':'entry','default':0, 'label':'xlabel angle'},
                'use_index':{'type':'checkbox','default':1,'label':'use index'},
                'errorbars':{'type':'checkbox','default':0,'label':'errorbar column'},
                'clrcol':{'type':'combobox','items':datacols,'label':'color by value','default':''},
                'cscale':{'type':'combobox','items':scales,'label':'color scale','default':'linear'},
                'colorbar':{'type':'checkbox','default':0,'label':'show colorbar'},
                'bw':{'type':'checkbox','default':0,'label':'black & white'},
                'showxlabels':{'type':'checkbox','default':1,'label':'x tick labels'},
                'showylabels':{'type':'checkbox','default':1,'label':'y tick labels'},
                'sharex':{'type':'checkbox','default':0,'label':'share x'},
                'sharey':{'type':'checkbox','default':0,'label':'share y'},
                'legend':{'type':'checkbox','default':1,'label':'legend'},
                #'loc':{'type':'combobox','default':'best','items':self.legendlocs,'label':'legend loc'},
                'kind':{'type':'combobox','default':'line','items':self.kinds,'label':'plot type'},
                'stacked':{'type':'checkbox','default':0,'label':'stacked'},
                'linewidth':{'type':'slider','default':1.5,'range':(0,10),'interval':0.1,'label':'line width'},
                'alpha':{'type':'slider','default':0.9,'range':(0,1),'interval':0.1,'label':'alpha'},
                'subplots':{'type':'checkbox','default':0,'label':'multiple subplots'},
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
        #size = self.kwds['fontsize']
        #plt.rc("font", family=self.kwds['font'], size=size)
        #plt.rc('legend', fontsize=size-1)
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

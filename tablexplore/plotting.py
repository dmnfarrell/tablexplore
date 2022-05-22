#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    tableexplore plotting module
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
import sys,os,random,platform
from collections import OrderedDict

import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.lines import Line2D
try:
    from pandas import plotting
except ImportError:
    from pandas.tools import plotting
import numpy as np
import pandas as pd
from .qt import *
from .dialogs import *
from . import util
import logging

homepath = os.path.expanduser("~")
module_path = os.path.dirname(os.path.abspath(__file__))
iconpath = os.path.join(module_path, 'icons')
settingspath = os.path.join(homepath, '.config','tablexplore')
cmapsfile = os.path.join(settingspath, 'cmaps.pkl')

colormaps = sorted(m for m in plt.cm.datad if not m.endswith("_r"))
markers = ['','o','.','^','v','>','<','s','+','x','p','d','h','*']
linestyles = ['-','--','-.',':']
plotkinds = ['line', 'bar', 'barh', 'scatter', 'pie', 'histogram', 'boxplot', 'violinplot', 'dotplot',
             'heatmap', 'area', 'hexbin', 'scatter_matrix', 'density', 'radviz']
valid_kwds = {'line': ['alpha', 'colormap', 'grid', 'legend', 'linestyle','ms',
                  'linewidth', 'marker', 'subplots', 'rotx', 'logx', 'logy',
                  'sharex','sharey', 'kind'],
            'scatter': ['alpha', 'grid', 'linewidth', 'marker', 'subplots', 'ms',
                    'legend', 'colormap','sharex','sharey', 'logx', 'logy', 'use_index',
                    'clrcol', 'cscale','colorbar','bw','labelcol','pointsizes'],
            'pie': ['colormap','legend'],
            'hexbin': ['alpha', 'colormap', 'grid', 'linewidth','subplots','bins'],
            'bootstrap': ['grid'],
            'bar': ['alpha', 'colormap', 'grid', 'legend', 'linewidth', 'subplots',
                    'sharex','sharey', 'logy', 'stacked', 'rotx', 'kind', 'edgecolor'],
            'barh': ['alpha', 'colormap', 'grid', 'legend', 'linewidth', 'subplots',
                    'sharex','sharey','stacked', 'rotx', 'kind', 'logx', 'edgecolor'],
            'histogram': ['alpha', 'linewidth','grid','stacked','subplots','colormap',
                     'sharex','sharey','rotx','bins', 'logx', 'logy', 'legend', 'edgecolor'],
            'heatmap': ['colormap','colorbar','rotx', 'linewidth','linestyle',
                        'subplots','rotx','cscale','bw','alpha','sharex','sharey'],
            'area': ['alpha','colormap','grid','linewidth','legend','stacked',
                     'kind','rotx','logx','sharex','sharey','subplots'],
            'density': ['alpha', 'colormap', 'grid', 'legend', 'linestyle',
                         'linewidth', 'marker', 'subplots', 'rotx', 'kind'],
            'boxplot': ['rotx','grid','logy','colormap','alpha','linewidth','legend',
                        'subplots','edgecolor','sharex','sharey'],
            'violinplot': ['rotx','grid','logy','colormap','alpha','linewidth','legend',
                        'subplots','edgecolor','sharex','sharey'],
            'dotplot': ['marker','edgecolor','linewidth','colormap','alpha','legend',
                        'subplots','ms','bw','logy','sharex','sharey'],
            'scatter_matrix':['alpha', 'linewidth', 'marker', 'grid', 's'],
            'contour': ['linewidth','colormap','alpha','subplots'],
            'imshow': ['colormap','alpha'],
            'venn': ['colormap','alpha'],
            'radviz': ['linewidth','marker','edgecolor','s','colormap','alpha']
            }

def defaultOptions():
    """Get default plotting options"""

    opts = {'general': MPLBaseOptions(),
            'format': FormatOptions(),
            'labels': AnnotationOptions(),
            'axes': AxesOptions()
            }
    return opts

def update_colormaps():
    """Load stored colormaps"""

    cmaps = load_colormaps()
    if cmaps == None:
        return
    for name in cmaps:
        cm=cmaps[name]
        mpl.colormaps.register(cm)
        global colormaps
        colormaps.append(cm.name)
    return

def load_colormaps():

    if not os.path.exists(cmapsfile):
        return {}
    import pickle
    fp = open(cmapsfile, 'rb')
    cmaps = pickle.load(fp)
    fp.close()
    return cmaps

class PlotWidget(FigureCanvas):
    def __init__(self, parent=None, figure=None, dpi=100, hold=False):

        if figure == None:
            figure = Figure()
        super(PlotWidget, self).__init__(figure)
        self.setParent(parent)
        self.figure = Figure(dpi=dpi)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

class PlotViewer(QWidget):
    """Plot viewer class"""
    def __init__(self, table, parent=None):

        super(PlotViewer, self).__init__(parent)
        self.parent = parent
        self.table = table
        self.createWidgets()
        self.createOptions()
        #self.seriesopts = SeriesOptions(plotviewer=self)
        self.currentdir = os.path.expanduser('~')
        sizepolicy = QSizePolicy()
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.style = None
        return

    def addPlotWidget(self):
        """Create mpl plot canvas and toolbar"""

        layout = self.left
        vbox = self.vbox
        self.canvas = PlotWidget(layout)
        self.fig = self.canvas.figure
        self.ax = self.canvas.ax
        self.toolbar = NavigationToolbar(self.canvas, layout)

        #add custom buttons
        #iconfile = os.path.join(iconpath,'plotseries.png')
        #a = QAction(QIcon(iconfile), "Customise Series", self)
        #a.triggered.connect(self.customiseSeries)
        #self.toolbar.addAction(a)
        iconfile = os.path.join(iconpath,'reduce.png')
        a = QAction(QIcon(iconfile), "Reduce elements",  self)
        a.triggered.connect(lambda: self.zoom(zoomin=False))
        self.toolbar.addAction(a)
        iconfile = os.path.join(iconpath,'enlarge.png')
        a = QAction(QIcon(iconfile), "Enlarge elements",  self)
        a.triggered.connect(lambda: self.zoom(zoomin=True))
        self.toolbar.addAction(a)
        vbox.addWidget(self.toolbar)
        vbox.addWidget(self.canvas)
        return

    def updateSeries(self, event=None):
        """Update series with new plots"""

        data = self.table.getSelectedDataFrame()
        self.seriesopts.series = self.getSeries(data)
        return

    def customiseSeries(self):
        """
        Show custom options for current plot series. Allows plot types to
        be specified per series and uses a custom plot function.
        """

        if self.seriesopts.series == {}:
            self.updateSeries()
        dlg = self.seriesopts.showDialog(self)
        dlg.exec_()
        return

    def customPlot(self):
        """plot custom series """

        self.applyPlotoptions()
        self.setStyle()
        kwds = self.opts['general'].kwds
        formatkwds = self.opts['format'].kwds
        kwds.update(formatkwds)
        axes_layout = kwds['axes_layout']
        lkwds = self.opts['labels'].kwds.copy()
        axkwds = self.opts['axes'].kwds

        data = self.table.getSelectedDataFrame()
        layout='single'
        self.clear()
        self.ax = self.fig.add_subplot(111)
        series = self.seriesopts.series
        for s in series:
            df = data[s]
            skwds = series[s]
            kind = skwds['kind']
            #skwds = self.check_kwds(skwds, kind)
            #print (skwds)
            df.plot(layout=layout,ax=self.ax,**skwds)
        self.fig.legend()

        axs=self.ax
        lkwds.update(kwds)
        self.setFigureOptions(axs, lkwds)
        self.canvas.draw()
        return

    def check_kwds(self, kwds, kind):
        return dict((k, kwds[k]) for k in valid_kwds[kind] if k in kwds)

    def colorsfromColormap(self, df, cmap):
        """Column colors from cmap"""

        cols = df.columns
        clrs = util.gen_colors(cmap,len(cols))
        colordict = dict(zip(cols,clrs))
        return colordict

    def showTools(self):
        """Show/hide tools dock"""

        if self.dock.isHidden():
            self.dock.show()
        else:
            self.dock.hide()
        return

    def createWidgets(self):
        """Create widgets. Plot on left and dock for tools on right."""

        self.main = QWidget(self)
        hbox = QHBoxLayout(self)
        self.left = left = QWidget(self.main)
        hbox.addWidget(left)
        self.vbox = vbox = QVBoxLayout(left)
        self.addPlotWidget()
        return

    def setFigure(self, figure):
        """Recreate canvas with given figure"""

        self.clear()
        self.canvas.figure = figure
        self.fig = self.canvas.figure
        self.ax = self.canvas.ax
        self.canvas.draw()
        return

    def getFigureSize(self):

        fig=self.fig
        size = fig.get_size_inches()
        return size

    def createOptions(self):
        """Create option attributes for plotter"""

        self.opts = {'general':MPLBaseOptions(),
                    'format':FormatOptions(),
                    'labels':AnnotationOptions(),
                    'axes':AxesOptions()
                    }
        return

    def simple_plot(self, df):
        """test plot"""

        kwds = self.opts['general'].kwds
        self.ax = self.fig.add_subplot(111)
        cols = df.columns
        x=df[cols[0]]
        y=df[cols[1]]
        cmap = plt.cm.get_cmap(kwds['colormap'])
        self.ax.scatter(x, y, s=kwds['ms']*10, marker=kwds['marker'] )
        self.canvas.draw()
        return

    def zoom(self, zoomin=True):
        """Zoom in/out to plot by changing size of elements"""

        if zoomin == False:
            val=-1.0
        else:
            val=1.0

        if len(self.opts['general'].kwds) == 0:
            return

        self.opts['format'].increment('linewidth',val/5)
        self.opts['format'].increment('ms',val)
        self.opts['labels'].increment('fontsize',val)
        self.replot()
        return

    def clear(self):

        self.canvas.axes.clear()
        self.canvas.draw()
        return

    def plot(self):
        self.replot()

    def replot(self, data=None):
        """Replot with given dataframe"""

        self.clear()
        if data is None:
            self.data = self.table.getSelectedDataFrame()
        else:
            self.data = data

        self.applyPlotoptions()
        #self.updateSeries()
        self.setStyle()
        self.plotCurrent()
        return

    def plotCurrent(self, redraw=True):
        """Plot the current data"""

        #set some mpl defaults
        mpl.rcParams['grid.linestyle'] = '--'
        mpl.rcParams['grid.linewidth'] = 1

        #plot3d = self.opts['general'].kwds['3D plot']
        self._initFigure()
        #if plot3d == 1:
        #    self.plot3D(redraw=redraw)
        #else:
        self.plot2D(redraw=redraw)
        return

    def getSeries(self, data):

        kwds = self.opts['general'].kwds
        fkwds = self.opts['format'].kwds
        kwds.update(fkwds)
        self.series = series = {}
        colordict = self.colorsfromColormap(data, fkwds['colormap'])
        #print (colordict)
        basekwds = ['kind','marker','ms','linestyle', 'linewidth', 'alpha']
        skwds = {k:kwds[k] for k in basekwds}
        #print (fkwds)
        for c in data.columns:
            series[c] = skwds.copy()
            #series[c]['kind'] = kind
            series[c]['color'] = colordict[c]
            print (series[c])
        print (self.series)
        return series

    def applyPlotoptions(self):
        """Apply the current plotter/options"""

        for name in self.opts:
            self.opts[name].applyOptions()

        self.style = self.opts['format'].kwds['style']
        return

    def updateData(self):
        """Update data widgets"""

        if self.table is None:
            return
        df = self.table.model.df
        self.opts['general'].update(df)
        #self.opts['series'].update(df)
        return

    def clear(self):
        """Clear plot"""

        self.fig.clear()
        self.ax = None
        self.canvas.draw()
        self.table.plotted=None
        self.gridaxes = {}
        return

    def savePlot(self, filename=None):
        """Save the current plot"""

        ftypes = [('png','*.png'),('jpg','*.jpg'),('tif','*.tif'),('pdf','*.pdf'),
                    ('eps','*.eps'),('svg','*.svg')]
        if filename == None:
            filename, _ = QFileDialog.getSaveFileName(self,"Save Project",
                                              "","png files (*.png);;jpg files (*.jpg)")
        if filename:
            self.currentdir = os.path.dirname(os.path.abspath(filename))
            #dpi = self.globalopts['dpi']
            self.fig.savefig(filename, dpi=core.DPI)
        return

    def showWarning(self, text='plot error', ax=None):
        """Show warning message in the plot window"""

        if ax==None:
            ax = self.fig.add_subplot(111)
        ax.clear()
        ax.text(.5, .5, text, transform=self.ax.transAxes,
                       horizontalalignment='center', color='blue', fontsize=16)
        self.canvas.draw()
        return

    def _initFigure(self):
        """Clear figure or add a new axis to existing layout"""

        from matplotlib.gridspec import GridSpec
        #plot3d = self.opts['general'].kwds['3D plot']
        plot3d = 0
        if plot3d == 1:
            #self.canvas.close()
            #self.toolbar.close()
            #self.addPlotWidget()
            self.ax = self.fig.add_subplot(1, 1, 1, projection='3d',label='3d')
            self.ax.mouse_init()
            print (self.ax)
        else:
            #default layout is just a single axis
            self.fig.clear()
            self.gridaxes = {}
            self.ax = self.fig.add_subplot(111)

        return

    def plot2D(self, redraw=True):
        """Plot method for current data. Relies on pandas plot functionality
           if possible. There is some temporary code here to make sure only the valid
           plot options are passed for each plot kind."""

        if not hasattr(self, 'data'):
            return

        data = self.data
        #print (data)
        data.columns = self.checkColumnNames(data.columns)

        #get all options from the mpl options object
        kwds = self.opts['general'].kwds
        formatkwds = self.opts['format'].kwds
        kwds.update(formatkwds)
        axes_layout = kwds['axes_layout']
        lkwds = self.opts['labels'].kwds.copy()
        axkwds = self.opts['axes'].kwds

        kind = kwds['kind']
        by = kwds['by']
        by2 = kwds['by2']
        errorbars = kwds['errorbars']
        useindex = kwds['use_index']
        bw = kwds['bw']
        style = kwds['style']

        nrows = axkwds['rows']
        ncols = axkwds['cols']

        if self._checkNumeric(data) == False and kind != 'venn':
            self.showWarning('no numeric data to plot')
            return

        kwds['edgecolor'] = 'black'
        #valid kwd args for this plot type
        kwargs = dict((k, kwds[k]) for k in valid_kwds[kind] if k in kwds)

        ax = self.ax

        if by != '':
            #groupby needs to be handled per group so we can create the axes
            #for our figure and add them outside the pandas logic
            if by not in data.columns:
                self.showWarning('the grouping column must be in selected data')
                return
            if by2 != '' and by2 in data.columns:
                by = [by,by2]
            g = data.groupby(by)

            if axes_layout == 'multiple':
                i=1
                if len(g) > 30:
                    self.showWarning('%s is too many subplots' %len(g))
                    return
                size = len(g)
                if nrows == 0:
                    nrows = int(np.sqrt(size))
                    ncols = int(np.ceil(size/nrows))

                self.ax.set_visible(False)
                kwargs['subplots'] = None
                for n,df in g:
                    if ncols==1 and nrows==1:
                        ax = self.fig.add_subplot(111)
                        self.ax.set_visible(True)
                    else:
                        ax = self.fig.add_subplot(nrows,ncols,i)
                    kwargs['legend'] = False #remove axis legends
                    d = df.drop(by,1) #remove grouping columns
                    axs = self._doplot(d, ax, kind, 'single',  errorbars, useindex,
                                  bw=bw, yerr=None, nrows=0, ncols=0, kwargs=kwargs)
                    ax.set_title(n)
                    handles, labels = ax.get_legend_handles_labels()
                    i+=1

                if 'sharey' in kwargs and kwargs['sharey'] == True:
                    self.autoscale()
                if  'sharex' in kwargs and kwargs['sharex'] == True:
                    self.autoscale('x')
                self.fig.legend(handles, labels, loc='center right', #bbox_to_anchor=(0.9, 0),
                                 bbox_transform=self.fig.transFigure )
                axs = self.fig.get_axes()

            else:
                kwargs['subplots'] = 0
                #single plot grouped only apply to some plot kinds
                #the remainder are not supported
                axs = self.ax
                labels = []; handles=[]
                cmap = plt.cm.get_cmap(kwargs['colormap'])
                #handle as pivoted data for some line, bar
                data = data.apply( lambda x: pd.to_numeric(x,errors='ignore',downcast='float') )
                if kind in ['line','bar','barh']:
                    df = pd.pivot_table(data,index=by)
                    errs = data.groupby(by).std()
                    self._doplot(df, axs, kind, axes_layout, errorbars, useindex=None, yerr=errs,
                                      bw=bw, nrows=0, ncols=0, kwargs=kwargs)
                elif kind == 'scatter':
                    #we plot multiple groups and series in different colors
                    #this logic could be placed in the scatter method?
                    d = data.drop(by,1)
                    d = d._get_numeric_data()
                    xcol = d.columns[0]
                    ycols = d.columns[1:]
                    c=0
                    legnames = []
                    handles = []
                    slen = len(g)*len(ycols)
                    clrs = [cmap(float(i)/slen) for i in range(slen)]
                    for n, df in g:
                        for y in ycols:
                            kwargs['color'] = clrs[c]
                            currax, sc = self.scatter(df[[xcol,y]], ax=axs, **kwargs)
                            if type(n) is tuple:
                                n = ','.join(n)
                            legnames.append(','.join([n,y]))
                            handles.append(sc[0])
                            c+=1
                    if kwargs['legend'] == True:
                        if slen>6:
                            lc = int(np.round(slen/10))
                        else:
                            lc = 1
                        axs.legend([])
                        axs.legend(handles, legnames, ncol=lc)
                else:
                    self.showWarning('single grouped plots not supported for %s\n'
                                     'try using multiple subplots' %kind)
        else:
            #special case of twin axes
            if axes_layout == 'twin axes':
                self.ax.set_visible(False)
                ax = self.fig.add_subplot(111)
                #ax.get_xaxis().set_ticks([])
                #ax.get_yaxis().set_ticks([])
                if kind != 'line':
                    self.showWarning('twin axes only supported for line plots')
                    return
                lw = kwds['linewidth']
                bw = kwds['bw']
                marker = kwds['marker']
                ms = kwds['ms']
                ls = kwds['linestyle']

                if useindex == False:
                    data = data.set_index(data.columns[0])
                cols = list(data.columns)
                twinaxes = [ax]
                if len(cols)>1:
                    for i in range(len(cols)-1):
                        twinaxes.append(ax.twinx())

                styles = []
                cmap = plt.cm.get_cmap(kwds['colormap'])

                i=0
                handles=[]
                for col in cols:
                    d = data[col]
                    cax = twinaxes[i]
                    clr = cmap(float(i+1)/(len(cols)))
                    d.plot(ax=cax, kind='line', c=clr, style=styles, linewidth=lw,
                            linestyle=ls, marker=marker, ms=ms, legend=False, grid=False)
                    if i>1:
                        cax.spines["right"].set_position(("axes", 1+i/20))
                    cax.set_ylabel(col)
                    handles.append(cax.get_lines()[0])
                    #if i>=1:
                    #    cax.get_xaxis().set_ticklabels([])
                    i+=1

                ax.legend(handles, cols, loc='best')
                self._setAxisTickFormat(ax)
                self.ax=axs=ax
            else:
                #default plot - mostly uses pandas so we directly call _doplot
                try:
                    axs = self._doplot(data, ax, kind, axes_layout, errorbars,
                                       useindex, bw=bw, yerr=None, nrows=nrows, ncols=ncols,
                                       kwargs=kwargs)
                except Exception as e:
                    self.showWarning(e)
                    logging.error("Exception occurred", exc_info=True)
                    return

        #set options general for all plot types
        #annotation optons are separate
        lkwds.update(kwds)
        self.setFigureOptions(axs, lkwds)
        scf = 12/lkwds['fontsize']
        try:
            self.fig.tight_layout()
            self.fig.subplots_adjust(top=0.9)
            if by != '':
                self.fig.subplots_adjust(right=0.9)
        except:
            self.fig.subplots_adjust(left=0.1, right=0.9, top=0.89,
                                     bottom=0.1, hspace=.4/scf, wspace=.2/scf)
            print ('tight_layout failed')

        #set axes formats
        self._setAxisRanges()
        if axes_layout == 'multiple':
            for ax in self.fig.axes:
                self._setAxisTickFormat(ax)
        else:
            self._setAxisTickFormat(self.ax)

        if style == 'dark_background':
            self.fig.set_facecolor('black')
        else:
            self.fig.set_facecolor('white')
        if redraw == True:
            self.canvas.draw()
        return

    def plotBySeries(self):
        """Plot different types depending on series"""

        #for s in series:

        return

    def setFigureOptions(self, axs, kwds):
        """Set axis wide options such as ylabels, title"""

        if type(axs) is np.ndarray:
            self.ax = axs.flat[0]
        elif type(axs) is list:
            self.ax = axs[0]
        self.fig.suptitle(kwds['title'], fontsize=kwds['fontsize']*1.2)

        axes_layout = kwds['axes_layout']
        if axes_layout == 'multiple':
            for ax in self.fig.axes:
                self.setAxisLabels(ax, kwds)
        else:
            self.setAxisLabels(self.ax, kwds)
        return

    def setAxisLabels(self, ax, kwds):
        """Set a plots axis labels"""

        if kwds['xlabel'] != '':
            ax.set_xlabel(kwds['xlabel'])
        if kwds['ylabel'] != '':
            ax.set_ylabel(kwds['ylabel'])
        ax.xaxis.set_visible(kwds['showxlabels'])
        ax.yaxis.set_visible(kwds['showylabels'])
        if kwds['rotx'] != 0:
            for tick in ax.get_xticklabels():
                tick.set_rotation(kwds['rotx'])
        return

    def autoscale(self, axis='y'):
        """Set all subplots to limits of largest range"""

        l=None
        u=None
        for ax in self.fig.axes:
            if axis=='y':
                a, b  = ax.get_ylim()
            else:
                a, b  = ax.get_xlim()
            if l == None or a<l:
                l=a
            if u == None or b>u:
                u=b
        lims = (l, u)
        #print (lims)
        for a in self.fig.axes:
            if axis=='y':
                a.set_ylim(lims)
            else:
                a.set_xlim(lims)
        return

    def _clearArgs(self, kwargs):
        """Clear kwargs of formatting options so that a style can be used"""

        keys = ['colormap','grid']
        for k in keys:
            if k in kwargs:
                kwargs[k] = None
        return kwargs

    def _doplot(self, data, ax, kind, axes_layout, errorbars, useindex, bw, yerr,
                nrows, ncols, kwargs):
        """Core plotting method where the individual plot functions are called"""

        kwargs = kwargs.copy()

        if 'alpha' in kwargs:
            kwargs['alpha'] = kwargs['alpha']

        cols = data.columns
        if kind == 'line':
            data = data.sort_index()

        #calculate required rows
        rows = int(round(np.sqrt(len(data.columns)),0))
        if len(data.columns) == 1 and kind not in ['pie']:
            kwargs['subplots'] = 0

        if 'colormap' in kwargs:
            cmap = plt.cm.get_cmap(kwargs['colormap'])
        else:
            cmap = None
        #change some things if we are plotting in b&w
        styles = []
        if bw == True and kind not in ['pie','heatmap']:
            cmap = None
            kwargs['color'] = 'k'
            kwargs['colormap'] = None
            styles = ["-","--","-.",":"]
            if 'linestyle' in kwargs:
                del kwargs['linestyle']

        if axes_layout == 'single':
            layout = None
        elif nrows != 0:
            #override automatic rows/cols with widget options
            layout = (nrows,ncols)
            kwargs['subplots'] = 1
        else:
            layout = (rows,-1)
            kwargs['subplots'] = 1

        if errorbars == True and yerr == None:
            yerr = data[data.columns[1::2]]
            data = data[data.columns[0::2]]
            yerr.columns = data.columns
            plt.rcParams['errorbar.capsize']=4

        if kind == 'bar' or kind == 'barh':
            if len(data) > 50:
                ax.get_xaxis().set_visible(False)
            if len(data) > 300:
                self.showWarning('too many bars to plot')
                return
        if kind == 'scatter':
            axs, sc = self.scatter(data, ax, axes_layout, **kwargs)
            if kwargs['sharey'] == 1:
                lims = self.fig.axes[0].get_ylim()
                for a in self.fig.axes:
                    a.set_ylim(lims)
        elif kind == 'boxplot':
            axs = data.boxplot(ax=ax, grid=kwargs['grid'],
                               patch_artist=True, return_type='dict')
            lw = kwargs['linewidth']
            plt.setp(axs['boxes'], color='black', lw=lw)
            plt.setp(axs['whiskers'], color='black', lw=lw)
            plt.setp(axs['fliers'], color='black', marker='+', lw=lw)
            clr = cmap(0.5)
            for patch in axs['boxes']:
                patch.set_facecolor(clr)
            if kwargs['logy'] == 1:
                ax.set_yscale('log')
        elif kind == 'violinplot':
            axs = self.violinplot(data, ax, kwargs)
        elif kind == 'dotplot':
            axs = self.dotplot(data, ax, kwargs)

        elif kind == 'histogram':
            #bins = int(kwargs['bins'])
            axs = data.plot(kind='hist',layout=layout, ax=ax, **kwargs)
        elif kind == 'heatmap':
            if len(data) > 1000:
                self.showWarning('too many rows to plot')
                return
            axs = self.heatmap(data, ax, kwargs)
        elif kind == 'bootstrap':
            axs = plotting.bootstrap_plot(data)
        elif kind == 'scatter_matrix':
            kwargs['marker'] = 'o'
            kwargs['s'] = 2
            axs = plotting.scatter_matrix(data, ax=ax, **kwargs)
        elif kind == 'hexbin':
            x = cols[0]
            y = cols[1]
            bins = int(kwargs['bins'])
            axs = data.plot(x,y,ax=ax,kind='hexbin',gridsize=bins,**kwargs)
        elif kind == 'contour':
            xi,yi,zi = self.contourData(data)
            cs = ax.contour(xi,yi,zi,15,linewidths=.5,colors='k')
            #plt.clabel(cs,fontsize=9)
            cs = ax.contourf(xi,yi,zi,15,cmap=cmap)
            self.fig.colorbar(cs,ax=ax)
            axs = ax
        elif kind == 'imshow':
            xi,yi,zi = self.contourData(data)
            im = ax.imshow(zi, interpolation="nearest",
                           cmap=cmap, alpha=kwargs['alpha'])
            self.fig.colorbar(im,ax=ax)
            axs = ax
        elif kind == 'pie':
            if useindex == False:
                x=data.columns[0]
                data.set_index(x,inplace=True)
            if kwargs['legend'] == True:
                lbls=None
            else:
                lbls = list(data.index)
            kwargs['subplots'] = True
            kwargs['legend'] = False
            axs = data.plot(ax=ax, kind='pie', labels=lbls, layout=layout,
                            autopct='%1.1f%%', **kwargs)
            if lbls == None:
                self.fig.legend(labels=data.index)
        elif kind == 'venn':
            axs = self.venn(data, ax, **kwargs)
        elif kind == 'radviz':
            if kwargs['marker'] == '':
                kwargs['marker'] = 'o'
            col = data.columns[-1]
            axs = pd.plotting.radviz(data, col, ax=ax, **kwargs)
        else:
            #line, bar and area plots
            if useindex == False:
                x=data.columns[0]
                data.set_index(x,inplace=True)
            if len(data.columns) == 0:
                msg = "Not enough data.\nIf 'use index' is off select at least 2 columns"
                self.showWarning(msg)
                return
            #adjust colormap to avoid white lines
            if cmap != None:
                #cmap = util.adjustColorMap(cmap, 0.15,1.0)
                del kwargs['colormap']
            if kind == 'barh':
                kwargs['xerr']=yerr
                yerr=None

            axs = data.plot(ax=ax, layout=layout, yerr=yerr, style=styles, cmap=cmap,
                             **kwargs)
        return axs

    def setStyle(self):
        """Apply style"""

        if self.style == None or self.style == '':
            mpl.rcParams.update(mpl.rcParamsDefault)
        else:
            plt.style.use(self.style)
        return

    def _setAxisRanges(self):

        kwds = self.opts['axes'].kwds
        ax = self.ax
        try:
            xmin=float(kwds['xmin'])
            xmax=float(kwds['xmax'])
            ax.set_xlim((xmin,xmax))
        except:
            pass
        try:
            ymin=float(kwds['ymin'])
            ymax=float(kwds['ymax'])
            ax.set_ylim((ymin,ymax))
        except:
            pass
        return

    def _setAxisTickFormat(self, ax):
        """Set axis tick format"""

        import matplotlib.ticker as mticker
        import matplotlib.dates as mdates
        kwds = self.opts['axes'].kwds
        #ax = self.ax
        data = self.data
        cols = list(data.columns)
        x = data[cols[0]]
        xt = kwds['major x-ticks']
        yt = kwds['major y-ticks']
        xmt = kwds['minor x-ticks']
        ymt = kwds['minor y-ticks']
        symbol = kwds['symbol']
        places = kwds['precision']
        dateformat = kwds['date format']

        if xt != 0:
            ax.xaxis.set_major_locator(mticker.MaxNLocator(nbins=xt))
        if yt != 0:
            ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=yt))
        if xmt != 0:
            ax.xaxis.set_minor_locator(mticker.AutoMinorLocator(n=xmt))
            ax.grid(b=True, which='minor', linestyle='--', linewidth=.5)
        if ymt != 0:
            ax.yaxis.set_minor_locator(mticker.AutoMinorLocator(n=ymt))
            ax.grid(b=True, which='minor', linestyle='--', linewidth=.5)
        formatter = kwds['formatter']
        if formatter == 'percent':
            ax.xaxis.set_major_formatter(mticker.PercentFormatter())
        elif formatter == 'eng':
            ax.xaxis.set_major_formatter(mticker.EngFormatter(unit=symbol,places=places))
        elif formatter == 'sci notation':
            ax.xaxis.set_major_formatter(mticker.LogFormatterSciNotation())
        elif formatter == 'date':
            locator = mdates.AutoDateLocator(minticks=4, maxticks=10)
            formatter = mdates.ConciseDateFormatter(locator)
            ax.xaxis.set_major_locator(locator)
            ax.xaxis.set_major_formatter(formatter)
        if dateformat != '':
            ax.xaxis.set_major_formatter(mdates.DateFormatter(dateformat))

        return

    def scatter(self, df, ax, axes_layout='single', alpha=0.8, marker='o', color=None, **kwds):
        """A custom scatter plot rather than the pandas one. By default this
        plots the first column selected versus the others"""

        if len(df.columns)<2:
            return
        data = df
        df = df.copy()._get_numeric_data()
        cols = list(df.columns)
        x = df[cols[0]]
        s=1
        cmap = plt.cm.get_cmap(kwds['colormap'])
        lw = kwds['linewidth']
        clrcol = kwds['clrcol']  #color by values in a column
        cscale = kwds['cscale']
        grid = kwds['grid']
        bw = kwds['bw']

        if cscale == 'log':
            norm = mpl.colors.LogNorm()
        else:
            norm = None
        if color != None:
            c = color
        elif clrcol != '':
            if clrcol in df.columns:
                if len(cols)>2:
                    cols.remove(clrcol)
            c = data[clrcol]
            if c.dtype.kind not in 'bifc':
                c = pd.factorize(c)[0]
        else:
            c = None
        plots = len(cols)
        if marker == '':
            marker = 'o'
        if axes_layout == 'multiple':
            size = plots-1
            nrows = int(round(np.sqrt(size),0))
            ncols = int(np.ceil(size/nrows))
            self.fig.clear()
        if c is not None:
            colormap = kwds['colormap']
        else:
            colormap = None
            c=None

        #print (kwds)
        labelcol = kwds['labelcol']
        pointsizes = kwds['pointsizes']
        handles = []
        for i in range(s,plots):
            y = df[cols[i]]
            ec = 'black'
            if bw == True:
                clr = 'white'
                colormap = None
            else:
                clr = cmap(float(i)/(plots))
            if colormap != None:
                clr=None
            if marker in ['x','+'] and bw == False:
                ec = clr

            if axes_layout == 'multiple':
                ax = self.fig.add_subplot(nrows,ncols,i)
            if pointsizes != '' and pointsizes in df.columns:
                ms = df[pointsizes]
                s=kwds['ms']
                getsizes = lambda x : (((x-x.min())/float(x.max()-x.min())+1)*s)**2.3
                ms = getsizes(ms)
                #print (ms)
            else:
                ms = kwds['ms'] * 12
            sc = ax.scatter(x, y, marker=marker, alpha=alpha, linewidth=lw, c=c,
                       s=ms, edgecolors=ec, facecolor=clr, cmap=colormap,
                       norm=norm, label=cols[i], picker=True)

            if kwds['logx'] == 1:
                ax.set_xscale('log')
            if kwds['logy'] == 1:
                ax.set_yscale('log')

            #create proxy artist for markers so we can return these handles if needed
            mkr = Line2D([0], [0], marker=marker, alpha=alpha, ms=10, markerfacecolor=c,
                        markeredgewidth=lw, markeredgecolor=ec, linewidth=0)
            handles.append(mkr)
            ax.set_xlabel(cols[0])
            if grid == 1:
                ax.grid(True, linestyle='--')
            if axes_layout == 'multiple':
                ax.set_title(cols[i])
            if colormap is not None and kwds['colorbar'] == True:
                self.fig.colorbar(scplt, ax=ax)

            if labelcol != '':
                if not labelcol in data.columns:
                    self.showWarning('label column %s not in selected data' %labelcol)
                elif len(data)<1500:
                    for i, r in data.iterrows():
                        txt = r[labelcol]
                        if pd.isnull(txt) is True:
                            continue
                        ax.annotate(txt, (x[i],y[i]), xycoords='data',
                                    xytext=(5, 5), textcoords='offset points',)

        if kwds['legend'] == 1 and axes_layout == 'single':
            ax.legend(cols[1:])

        return ax, handles

    def violinplot(self, df, ax, kwds):
        """violin plot"""

        data=[]
        clrs=[]
        df = df._get_numeric_data()
        cols = len(df.columns)
        cmap = plt.cm.get_cmap(kwds['colormap'])
        for i,d in enumerate(df):
            clrs.append(cmap(float(i)/cols))
            data.append(df[d].values)
        lw = kwds['linewidth']
        alpha = kwds['alpha']
        parts = ax.violinplot(data, showextrema=False, showmeans=True)
        i=0
        for pc in parts['bodies']:
            pc.set_facecolor(clrs[i])
            pc.set_edgecolor('black')
            pc.set_alpha(alpha)
            pc.set_linewidth(lw)
            i+=1
        labels = df.columns
        ax.set_xticks(np.arange(1, len(labels) + 1))
        ax.set_xticklabels(labels)
        return

    def dotplot(self, df, ax, kwds):
        """Dot plot"""

        marker = kwds['marker']
        if marker == '':
            marker = 'o'
        cmap = plt.cm.get_cmap(kwds['colormap'])
        ms = kwds['ms']
        lw = kwds['linewidth']
        alpha = kwds['alpha']
        cols = len(df.columns)
        axs = df.boxplot(ax=ax, grid=False, return_type='dict')
        plt.setp(axs['boxes'], color='white')
        plt.setp(axs['whiskers'], color='white')
        plt.setp(axs['caps'], color='black', lw=lw)
        plt.setp(axs['medians'], color='black', lw=lw)
        np.random.seed(42)
        for i,d in enumerate(df):
            clr = cmap(float(i)/cols)
            y = df[d]
            x = np.random.normal(i+1, 0.04, len(y))
            ax.plot(x, y, c=clr, mec='k', ms=ms, marker=marker, alpha=alpha,
                    mew=lw, linestyle="None")
        if kwds['logy'] == 1:
            ax.set_yscale('log')
        return ax

    def heatmap(self, df, ax, kwds):
        """Plot heatmap"""

        X = df._get_numeric_data()
        clr='black'
        lw = kwds['linewidth']
        if lw==0:
            clr=None
            lw=None
        if kwds['cscale']=='log':
            norm=mpl.colors.LogNorm()
        else:
            norm=None
        hm = ax.pcolor(X, cmap=kwds['colormap'], edgecolor=clr,
                       linewidth=lw,alpha=kwds['alpha'],norm=norm)
        if kwds['colorbar'] == True:
            self.fig.colorbar(hm, ax=ax)
        ax.set_xticks(np.arange(0.5, len(X.columns)))
        ax.set_yticks(np.arange(0.5, len(X.index)))
        ax.set_xticklabels(X.columns, minor=False)
        ax.set_yticklabels(X.index, minor=False)
        ax.set_ylim(0, len(X.index))

        #from mpl_toolkits.axes_grid1 import make_axes_locatable
        #divider = make_axes_locatable(ax)
        return

    def venn(self, data, ax, colormap=None, alpha=0.8):
        """Plot venn diagram, requires matplotlb-venn"""

        try:
            from matplotlib_venn import venn2,venn3
        except:
            self.showWarning('requires matplotlib_venn')
            return
        l = len(data.columns)
        if l<2: return
        x = data.values[:,0]
        y = data.values[:,1]
        if l==2:
            labels = list(data.columns[:2])
            v = venn2([set(x), set(y)], set_labels=labels, ax=ax)
        else:
            labels = list(data.columns[:3])
            z = data.values[:,2]
            v = venn3([set(x), set(y), set(z)], set_labels=labels, ax=ax)
        ax.axis('off')
        ax.set_axis_off()
        return ax

    def contourData(self, data):
        """Get data for contour plot"""

        x = data.values[:,0]
        y = data.values[:,1]
        z = data.values[:,2]
        xi = np.linspace(x.min(), x.max())
        yi = np.linspace(y.min(), y.max())
        zi = griddata(x, y, z, xi, yi, interp='linear')
        return xi,yi,zi

    def meshData(self, x,y,z):
        """Prepare 1D data for plotting in the form (x,y)->Z"""

        xi = np.linspace(x.min(), x.max())
        yi = np.linspace(y.min(), y.max())
        zi = griddata(x, y, z, xi, yi, interp='linear')
        X, Y = np.meshgrid(xi, yi)
        return X,Y,zi

    def getcmap(self, name):
        try:
            return plt.cm.get_cmap(name)
        except:
            return plt.cm.get_cmap('Spectral')

    def getView(self):
        ax = self.ax
        if hasattr(ax,'azim'):
            azm=ax.azim
            ele=ax.elev
            dst=ax.dist
        else:
            return None,None,None
        return azm,ele,dst

    def plot3D(self, redraw=True):
        """3D plot"""

        if not hasattr(self, 'data') or len(self.data.columns)<3:
            return
        kwds = self.opts['general'].kwds.copy()
        #use base options by joining the dicts
        #kwds.update(self.mplopts3d.kwds)
        kwds.update(self.opts['labels'].kwds)
        #print (kwds)
        data = self.data
        x = data.values[:,0]
        y = data.values[:,1]
        z = data.values[:,2]
        azm,ele,dst = self.getView()

        #self.fig.clear()
        ax = self.ax# = Axes3D(self.fig)
        kind = kwds['kind']
        #mode = kwds['mode']
        #rstride = kwds['rstride']
        #cstride = kwds['cstride']
        lw = kwds['linewidth']
        alpha = kwds['alpha']
        cmap = kwds['colormap']

        if kind == 'scatter':
            self.scatter3D(data, ax, kwds)
        elif kind == 'bar':
            self.bar3D(data, ax, kwds)
        elif kind == 'contour':
            from scipy.interpolate import griddata
            xi = np.linspace(x.min(), x.max())
            yi = np.linspace(y.min(), y.max())
            zi = griddata((x, y), z, (xi[None,:], yi[:,None]), method='cubic')
            surf = ax.contour(xi, yi, zi, rstride=rstride, cstride=cstride,
                              cmap=kwds['colormap'], alpha=alpha,
                              linewidth=lw, antialiased=True)
        elif kind == 'wireframe':
            if mode == '(x,y)->z':
                X,Y,zi = self.meshData(x,y,z)
            else:
                X,Y,zi = x,y,z
            w = ax.plot_wireframe(X, Y, zi, rstride=rstride, cstride=cstride,
                                  linewidth=lw)
        elif kind == 'surface':
            X,Y,zi = self.meshData(x,y,z)
            surf = ax.plot_surface(X, Y, zi, rstride=rstride, cstride=cstride,
                                   cmap=cmap, alpha=alpha,
                                   linewidth=lw)
            cb = self.fig.colorbar(surf, shrink=0.5, aspect=5)
            surf.set_clim(vmin=zi.min(), vmax=zi.max())
        #if kwds['points'] == True:
        #    self.scatter3D(data, ax, kwds)

        self.setFigureOptions(ax, kwds)
        if azm!=None:
            self.ax.azim = azm
            self.ax.elev = ele
            self.ax.dist = dst
        #handles, labels = self.ax.get_legend_handles_labels()
        #self.fig.legend(handles, labels)
        self.canvas.draw()
        return

    def bar3D(self, data, ax, kwds):
        """3D bar plot"""

        i=0
        plots=len(data.columns)
        cmap = plt.cm.get_cmap(kwds['colormap'])
        for c in data.columns:
            h = data[c]
            c = cmap(float(i)/(plots))
            ax.bar(data.index, h, zs=i, zdir='y', color=c)
            i+=1

    def scatter3D(self, data, ax, kwds):
        """3D scatter plot"""

        def doscatter(data, ax, color=None, pointlabels=None):
            data = data._get_numeric_data()
            l = len(data.columns)
            if l<3: return

            X = data.values
            x = X[:,0]
            y = X[:,1]
            handles=[]
            labels=data.columns[2:]
            for i in range(2,l):
                z = X[:,i]
                if color == None:
                    c = cmap(float(i)/(l))
                else:
                    c = color
                c='blue'
                h=ax.scatter(x, y, z, edgecolor='black', linewidth=lw, facecolor=c,
                           alpha=alpha, marker=marker, s=ms)
                handles.append(h)
            if pointlabels is not None:
                trans_offset = mtrans.offset_copy(ax.transData, fig=self.fig,
                                  x=0.05, y=0.10, units='inches')
                for i in zip(x,y,z,pointlabels):
                    txt=i[3]
                    ax.text(i[0],i[1],i[2], txt, None,
                    transform=trans_offset)

            return handles,labels

        lw = kwds['linewidth']
        alpha = kwds['alpha']/10
        ms = kwds['ms']*6
        marker = kwds['marker']
        if marker=='':
            marker='o'
        by = kwds['by']
        legend = kwds['legend']
        cmap = self.getcmap(kwds['colormap'])
        labelcol = kwds['labelcol']
        handles=[]
        pl=None
        if by != '':
            if by not in data.columns:
                self.showWarning('grouping column not in selection')
                return
            g = data.groupby(by)
            i=0
            pl=None
            for n,df in g:
                c = cmap(float(i)/(len(g)))
                if labelcol != '':
                    pl = df[labelcol]
                h,l = doscatter(df, ax, color=c, pointlabels=pl)
                handles.append(h[0])
                i+=1
            self.fig.legend(handles, g.groups)

        else:
            if labelcol != '':
                pl = data[labelcol]
            handles,lbls=doscatter(data, ax, pointlabels=pl)
            self.fig.legend(handles, lbls)
        return

    def checkColumnNames(self, cols):
        """Check length of column names"""

        from textwrap import fill
        try:
            cols = [fill(str(l), 25) for l in cols]
        except:
            logging.error("Exception occurred", exc_info=True)
        return cols

    def _checkNumeric(self, df):
        """Get only numeric data that can be plotted"""

        x = df.apply( lambda x: pd.to_numeric(x,errors='ignore',downcast='float') )
        if x.empty == True:
            return False


def addFigure(parent, figure=None, resize_callback=None):
    """Create a tk figure and canvas in the parent frame"""

    if figure == None:
        figure = Figure(figsize=(8,4), dpi=120, facecolor='white')

    canvas = FigureCanvas(figure=figure)
    canvas.setSizePolicy( QSizePolicy.Expanding,
                          QSizePolicy.Expanding)
    canvas.updateGeometry()
    return figure, canvas


class BaseOptions(object):
    """Class to generate widget dialog for dict of options"""
    def __init__(self):
        """Setup variables"""

        #self.parent = parent
        #opts is used to create the widgets
        #kwds is the dictionary where we store all the key:value pairs
        self.opts = {}
        self.style = '''
                    QWidget {
                        font-size: 12px;
                        max-width: 240px;
                    }
                    QLabel, QLineEdit {
                        min-width: 60px;
                    }
                    QPlainTextEdit {
                        max-height: 100px;
                        min-width: 100px;
                    }
                    QScrollBar:vertical {
                         width: 15px;
                     }
                    QComboBox {
                        combobox-popup: 0;
                        max-height: 30px;
                        max-width: 120px;
                    }
                '''
        return

    def setDefaults(self):
        """Populate default kwds dict"""

        self.kwds = {}
        for o in self.opts:
            self.kwds[o] = self.opts[o]['default']
        return

    def applyOptions(self):
        """Set the plot kwd arguments from the widgets"""

        self.kwds = getWidgetValues(self.widgets)
        return

    def apply(self):
        self.applyOptions()
        if self.callback != None:
            self.callback()
        return

    def showDialog(self, parent, wrap=2, section_wrap=2, style=None):
        """Auto create widgets for corresponding options and
           and return the dialog.
          Args:
            parent: parent frame
            wrap: wrap for internal widgets
        """

        self.style = style
        self.parent = parent
        dialog, widgets = dialogFromOptions(parent, self.opts, self.groups,
                                wrap=wrap, section_wrap=section_wrap, style=style)
        return dialog, widgets

    def setWidgetValue(self, key, value):

        setWidgetValues(self.widgets, {key: value})
        self.applyOptions()
        return

    def updateWidgets(self, kwds=None):
        """Update widgets from stored or supplied kwds"""

        if kwds==None:
            kwds = self.kwds
        for k in kwds:
            setWidgetValues(self.widgets, {k: kwds[k]})
        return

    def increment(self, key, inc):
        """Increase the value of a widget"""

        if not key in self.kwds:
            return
        new = self.kwds[key]+inc
        if new == 0:
            return
        self.setWidgetValue(key, new)
        return

    def randomSettings(self):
        """Get random settings"""

        kwds = self.kwds
        for k in kwds:
            opt = self.opts[k]
            if opt['type'] == 'combobox':
                kwds[k] = random.choice(opt['items'])
            elif opt['type'] == 'spinbox':
                if 'range' in opt.keys():
                    r=opt['range']
                    kwds[k] = random.randint(r[0],r[1])
        return

class MPLBaseOptions(BaseOptions):
    """Class to provide a dialog for matplotlib options and returning
        the selected prefs"""

    legendlocs = ['best','upper right','upper left','lower left','lower right','right','center left',
                'center right','lower center','upper center','center']

    def __init__(self):
        """Setup variables"""

        datacols=[]
        layouts = ['single','multiple','twin axes']
        scales = ['linear','log']
        grps = {'data':['by','by2','labelcol','pointsizes','clrcol'],
                'general':['kind','axes_layout','bins','stacked','use_index','errorbars',
                            'legend','sharex','sharey','logx','logy']
                }
                #'other':['3D plot']}
        order = ['general','data']
        self.groups = OrderedDict((key, grps[key]) for key in order)
        opts = self.opts = {
                'logx':{'type':'checkbox','default':0,'label':'log x'},
                'logy':{'type':'checkbox','default':0,'label':'log y'},
                'use_index':{'type':'checkbox','default':1,'label':'use index'},
                'errorbars':{'type':'checkbox','default':0,'label':'errorbar column'},
                'clrcol':{'type':'combobox','items':datacols,'label':'color by value','default':''},
                'bw':{'type':'checkbox','default':0,'label':'black & white'},
                'sharex':{'type':'checkbox','default':0,'label':'share x'},
                'sharey':{'type':'checkbox','default':0,'label':'share y'},
                'legend':{'type':'checkbox','default':1,'label':'legend'},
                'kind':{'type':'combobox','default':'line','items':plotkinds,'label':'plot type'},
                'stacked':{'type':'checkbox','default':0,'label':'stacked'},
                'axes_layout':{'type':'combobox','default':'single','items':layouts,'label':'axes layout'},
                'bins':{'type':'spinbox','default':20,'width':5},
                'by':{'type':'combobox','items':datacols,'label':'group by','default':''},
                'by2':{'type':'combobox','items':datacols,'label':'group by 2','default':''},
                'labelcol':{'type':'combobox','items':datacols,'label':'point labels','default':''},
                'pointsizes':{'type':'combobox','items':datacols,'label':'point sizes','default':''},
                 #'3D plot': {'type':'checkbox','default':0,'label':'3D plot'}
                }
        #self.kwds = {}
        self.setDefaults()
        return

    def update(self, df):
        """Update data widget(s) when dataframe changes"""

        if util.check_multiindex(df.columns) == 1:
            cols = list(df.columns.get_level_values(0))
        else:
            cols = list(df.columns)
        #add empty value
        cols = [str(c) for c in cols]
        cols = ['']+cols
        for name in ['by','by2','labelcol','clrcol']:
            self.widgets[name].clear()
            self.widgets[name].addItems(cols)
        return

class FormatOptions(BaseOptions):
    """This class also provides custom tools for adding items to the plot"""
    def __init__(self):
        """Setup variables"""

        scales = ['linear','log']
        style_list = ['default', 'classic', 'fivethirtyeight',
                     'seaborn-pastel','seaborn-whitegrid', 'ggplot','bmh',
                     'grayscale','dark_background']
        grps = {'styles':['style','colormap'],
                'formats':['marker','ms','linestyle','linewidth','alpha'],
                'axes':['grid','showxlabels','showylabels'],
                'colors':['bw','cscale','colorbar']
                }
        order = ['styles','formats','axes','colors']
        self.groups = OrderedDict((key, grps[key]) for key in order)
        opts = self.opts = {
                'style':{'type':'combobox','default':core.PLOTSTYLE,'items': style_list},
                'marker':{'type':'combobox','default':'','items': markers},
                'linestyle':{'type':'combobox','default':'-','items': linestyles},
                'linewidth':{'type':'doublespinbox','default':2.0,'range':(0,20),'interval':.2,'label':'line width'},
                'ms':{'type':'spinbox','default':5,'range':(1,80),'interval':1,'label':'marker size'},
                'grid':{'type':'checkbox','default':0,'label':'show grid'},
                'cscale':{'type':'combobox','items':scales,'label':'color scale','default':'linear'},
                'colorbar':{'type':'checkbox','default':0,'label':'show colorbar'},
                'bw':{'type':'checkbox','default':0,'label':'black & white'},
                'showxlabels':{'type':'checkbox','default':1,'label':'x tick labels'},
                'showylabels':{'type':'checkbox','default':1,'label':'y tick labels'},
                #'loc':{'type':'combobox','default':'best','items':self.legendlocs,'label':'legend loc'},
                'alpha':{'type':'doublespinbox','default':0.9,'range':(.1,1),'interval':.1,'label':'alpha'},
                'colormap':{'type':'combobox','default':'Spectral','items':colormaps},
                }
        self.setDefaults()
        return

class AnnotationOptions(BaseOptions):
    """This class also provides custom tools for adding items to the plot"""
    def __init__(self):
        """Setup variables"""

        from matplotlib import colors
        import six
        colors = list(six.iteritems(colors.cnames))
        colors = sorted([c[0] for c in colors])
        fillpatterns = ['-', '+', 'x', '\\', '*', 'o', 'O', '.']
        bstyles = ['square','round','round4','circle','rarrow','larrow','sawtooth']
        fonts = util.getFonts()
        if 'Windows' in platform.platform():
            defaultfont = 'Arial'
        else:
            defaultfont = 'FreeSans'
        fontweights = ['normal','bold','heavy','light','ultrabold','ultralight']
        alignments = ['left','center','right']
        colors = ['black','gray','red','blue','green','orange','purple','cyan','pink']

        #self.parent = parent
        self.groups = grps = {'global labels':['title','xlabel','ylabel','rotx'],
                             'format': ['font','fontsize','fontweight','color']
                             }
        self.groups = OrderedDict(sorted(grps.items()))
        opts = self.opts = {
                'title':{'type':'textarea','default':'','width':30},
                'xlabel':{'type':'entry','default':'','width':20},
                'ylabel':{'type':'entry','default':'','width':20},
                'facecolor':{'type':'combobox','default':'white','items': colors},
                'linecolor':{'type':'combobox','default':'black','items': colors},
                'fill':{'type':'combobox','default':'-','items': fillpatterns},
                'rotate':{'type':'scale','default':0,'range':(-180,180),'interval':1,'label':'rotate'},
                'boxstyle':{'type':'combobox','default':'square','items': bstyles},
                'text':{'type':'scrolledtext','default':'','width':20},
                #'align':{'type':'combobox','default':'center','items': alignments},
                'font':{'type':'font','default':defaultfont,'items':fonts},
                'fontsize':{'type':'spinbox','default':12,'range':(4,50),'label':'font size'},
                'fontweight':{'type':'combobox','default':'normal','items': fontweights},
                'color':{'type':'combobox','default':'black','items': colors},
                'rotx':{'type':'spinbox','default':0, 'range':(-180,180),'label':'xlabel angle'}
                }
        self.kwds = {}
        #used to store annotations
        self.textboxes = {}
        self.setDefaults()
        return

    def applyOptions(self):
        """Set the plot kwd arguments from the tk variables"""

        BaseOptions.applyOptions(self)
        from matplotlib.font_manager import FontProperties
        size = self.kwds['fontsize']
        #font = FontProperties()
        #font.set_family(self.kwds['font'])

        plt.rc("font", family=self.kwds['font'], size=size)#, weight=self.kwds['fontweight'])
        plt.rc('legend', fontsize=size-1)
        plt.rc('text', color=self.kwds['color'])
        return

class AxesOptions(BaseOptions):
    """Class for additional formatting options like styles"""
    def __init__(self):
        """Setup variables"""

        #self.parent = parent
        self.styles = sorted(plt.style.available)
        formats = ['auto','date','percent','eng','sci notation']
        datefmts = ['','%Y','%m','%d','%b','%d/%m/%Y','%d/%m/%y',
                    '%Y/%m/%d','%y/%m/%d','%Y/%d/%m',
                    '%d%m%Y','%Y%m%d','%Y%d%m',
                    '%d-%b-%Y',
                    '%Y-%m-%d %H:%M:%S','%Y-%m-%d %H:%M',
                    '%d-%m-%Y %H:%M:%S','%d-%m-%Y %H:%M'
                    ]
        self.groups = grps = OrderedDict({'main':['rows','cols','xmin','xmax','ymin','ymax',
                              'major x-ticks','major y-ticks','minor x-ticks','minor y-ticks',
                              'formatter','date format','symbol','precision'],
                             })
        opts = self.opts = {'rows':{'type':'spinbox','default':0},
                            'cols':{'type':'spinbox','default':0},
                            'xmin':{'type':'entry','default':'','label':'x min'},
                            'xmax':{'type':'entry','default':'','label':'x max'},
                            'ymin':{'type':'entry','default':'','label':'y min'},
                            'ymax':{'type':'entry','default':'','label':'y max'},
                            'major x-ticks':{'type':'spinbox','default':0},
                            'major y-ticks':{'type':'spinbox','default':0},
                            'minor x-ticks':{'type':'spinbox','default':0},
                            'minor y-ticks':{'type':'spinbox','default':0},
                            'formatter':{'type':'combobox','items':formats,'default':'auto'},
                            'symbol':{'type':'entry','default':''},
                            'precision':{'type':'entry','default':0},
                            'date format':{'type':'combobox','items':datefmts,'default':''}
                            }
        self.setDefaults()
        return

class SeriesOptions(BaseOptions):
    """Class for selecting custom plot types for each series"""
    def __init__(self, plotviewer):
        """Setup variables"""

        super(SeriesOptions, self).__init__()
        self.series = {}
        self.plotviewer = plotviewer
        self.setDefaults()
        return

    def showDialog(self, parent=None):

        dlg = self.dlg = SimpleDialog(parent, title='Series Options')
        self.createSeriesWidgets(dlg)
        btnbox = self.createButtons(dlg)
        return dlg

    def createButtons(self, parent):

        l = parent.layout
        bw = self.button_widget = QWidget(parent)
        vbox = QHBoxLayout(bw)
        button = QPushButton("Cancel")
        button.clicked.connect(self.close)
        vbox.addWidget(button)
        button = QPushButton("Clear")
        button.clicked.connect(self.update)
        vbox.addWidget(button)
        button = QPushButton("Update")
        button.clicked.connect(self.update)
        vbox.addWidget(button)
        l.addWidget(bw)
        return

    def createSeriesWidgets(self, parent):

        l = parent.layout
        l.setAlignment(QtCore.Qt.AlignTop)

        row = QWidget()
        l.addWidget(row)
        l2 = QHBoxLayout(row)
        for i in ['name','kind','color','line style','marker','marker size','alpha']:
            w=QLabel(i)
            l2.addWidget(w)
            #w.setFixedWidth(100)
        kinds = ['line','bar']
        self.widgets = {}
        for s in self.series:
            self.widgets[s] = {}
            opt=self.series[s]
            row = QWidget()
            l.addWidget(row)
            l2 = QHBoxLayout(row)
            w=QLabel(s)
            w.setFixedWidth(100)
            l2.addWidget(w)
            w=QComboBox()
            w.addItems(kinds)
            val = self.series[s]['kind']
            index = w.findText(val)
            w.setCurrentIndex(index)
            w.setFixedWidth(80)
            if val not in ['line','bar']:
                w.setEnabled(False)
            l2.addWidget(w)
            self.widgets[s]['kind'] = w
            w = ColorButton()
            val = self.series[s]['color']
            w.setColor(val)
            l2.addWidget(w)
            self.widgets[s]['color'] = w
            w=QComboBox()
            w.addItems(linestyles)
            val = self.series[s]['linestyle']
            index = w.findText(val)
            w.setCurrentIndex(index)
            l2.addWidget(w)
            self.widgets[s]['linestyle'] = w
            w=QSpinBox()
            val = self.series[s]['linewidth']
            w.setValue(int(val))
            l2.addWidget(w)
            self.widgets[s]['linewidth'] = w
            w=QComboBox()
            w.addItems(markers)
            val = self.series[s]['marker']
            index = w.findText(val)
            w.setCurrentIndex(index)
            self.widgets[s]['marker'] = w
            l2.addWidget(w)
            w=QSpinBox()
            val = self.series[s]['ms']
            w.setValue(int(val))
            l2.addWidget(w)
            self.widgets[s]['ms'] = w
            w=QDoubleSpinBox()
            val = self.series[s]['alpha']
            w.setValue(val)
            w.setRange(0,1)
            w.setSingleStep(0.1)
            l2.addWidget(w)
            self.widgets[s]['alpha'] = w

        return

    def update(self, event=None):
        """Update series options from widgets and replot"""

        for s in self.widgets:
            for i in self.widgets[s]:
                w = self.widgets[s][i]
                val = getWidgetValue(w)
                #print (s,i,val)
                self.series[s][i] = val
        #print (self.series)
        self.plotviewer.customPlot()
        return

    def close(self):
        self.dlg.destroy()
        return

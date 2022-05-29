"""

    Created May 2022
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
import inspect
import sys,os,platform,time,traceback
import pickle, gzip, random
from collections import OrderedDict
from tablexplore.qt import *
import numpy as np
import pandas as pd
from tablexplore import util, core, dialogs
from tablexplore.plugin import Plugin
import matplotlib as mpl
import pylab as plt
from tablexplore import plotting
import seaborn as sns

cmapsfile = core.cmapsfile

colormaps = sorted(m for m in plt.cm.datad if not m.endswith("_r"))
styles = ['darkgrid', 'whitegrid', 'dark', 'white', 'ticks']
kinds = ['point', 'bar', 'count', 'box', 'violin', 'strip']

class SeabornPlugin(Plugin):
    """Template plugin for TableExplore"""

    #uncomment capabilities list to appear in menu
    capabilities = ['gui']
    requires = ['']
    menuentry = 'Seaborn'
    iconfile = 'seaborn.png'
    name = 'Seaborn Plugin'

    def __init__(self, parent=None, table=None):
        """Customise this and/or doFrame for your widgets"""

        if parent==None:
            return
        self.parent = parent
        self.table = table

        self.createWidgets()
        return

    def _createMenuBar(self):
        """Create the menu bar for the application. """

        return

    def createWidgets(self):
        """Create widgets if GUI plugin"""

        df = self.table.table.model.df
        datacols = ['']+list(df.columns)
        self.opts = {'wrap': {'type':'entry','default':2,'label':'column wrap'},
                     'palette': {'type':'combobox','default':'Spectral','items':colormaps},
                     'kind': {'type':'combobox','default':'bar','items':kinds},
                     'col': {'type':'combobox','default':'','items':datacols},
                     'hue': {'type':'combobox','default':'','items':datacols},
                     'x': {'type':'combobox','default':'','items':datacols},
                     'y': {'type':'combobox','default':'','items':datacols},
                     'ci':{'type':'spinbox','default':95,'range':(0,100)},
                     'melt':{'type':'checkbox','default':1,'label':'long form'},
                     'fontscale':{'type':'doublespinbox','default':1.2,'range':(.5,3),
                                    'interval':.1, 'label':'font scale'},
                     #'title':{'type':'entry','default':''},
                     #'ylabel':{'type':'entry','default':''},
                     #'logy':{'type':'checkbox','default':0,'label':'log y'},
                     #'aspect':{'type':'doublespinbox','default':1.0, 'range':(-4,4)},
                     }

        grps = {'formats':['kind','wrap','palette'],
                    'factors':['x','y','hue','col','ci','melt'],
                    'labels':['fontscale']}
        self.groups = grps = OrderedDict(grps)

        self.main = QWidget()
        l = self.layout = QVBoxLayout()
        l.setSpacing(1)
        l.setAlignment(QtCore.Qt.AlignTop)
        self.main.setLayout(l)
        self.main.setMaximumWidth(300)
        dialog, self.widgets = dialogs.dialogFromOptions(self.main, self.opts, self.groups,
                            section_wrap=1)
        l.addWidget(dialog)
        bw = self.createButtons(self.main)
        l.addWidget(bw)
        return

    def createButtons(self, parent):

        bw = QWidget(parent)
        bw.setMaximumWidth(200)
        vbox = QVBoxLayout(bw)
        button = QPushButton("Plot")
        button.clicked.connect(self.replot)
        vbox.addWidget(button)
        return bw

    def replot(self, event=None):
        """Update the plot"""

        df = self.table.getSelectedDataFrame()
        print (df)
        kwds = dialogs.getWidgetValues(self.widgets)

        pf = self.table.pf
        figsize = pf.getFigureSize()
        height = figsize[1]
        plt.figure(figsize=figsize)

        keep = ['hue','col','x','y','palette','kind']
        kwargs = {i:kwds[i] for i in keep}
        for col in ['hue','col','x','y']:
            if kwargs[col] == '':
                del kwargs[col]
        print (kwargs)

        g = sns.catplot(data=df, height=height, aspect=1, **kwargs)
        self.g = g
        #except Exception as e:
        #    pf.showWarning(e)
        #    return
        pf.setFigure(g.fig)
        return

    def _update(self):
        """Update data widget(s)"""

        df = self.table.table.model.df
        datacols = ['']+list(df.columns)
        for key in ['x','y','hue','col']:
            self.widgets[key].clear()
            self.widgets[key].addItems(datacols)
        return

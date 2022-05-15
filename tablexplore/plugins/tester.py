"""

    Created January 2021
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
import pandas as pd
from tablexplore import util, core, dialogs
from tablexplore.plugin import Plugin
import pylab as plt

class ExamplePlugin(Plugin):
    """Template plugin for TableExplore"""

    #uncomment capabilities list to appear in menu
    capabilities = ['gui','docked']
    requires = ['']
    menuentry = 'Testing'
    iconfile = 'tests.png'
    name = 'Testing'

    def __init__(self, parent=None, table=None):
        """Customise this and/or doFrame for your widgets"""

        if parent==None:
            return
        self.parent = parent
        self.table = table
        self.ID = 'Testing'
        self.createWidgets()
        return

    def _createMenuBar(self):
        """Create the menu bar for the application. """

        return

    def createWidgets(self):
        """Create widgets if GUI plugin"""

        self.main = QWidget()
        l = self.layout = QHBoxLayout()
        l.setSpacing(1)
        l.setAlignment(QtCore.Qt.AlignTop)
        self.main.setLayout(l)
        bw = self.createButtons(self.main)
        l.addWidget(bw)
        return

    def createButtons(self, parent):

        bw = QWidget(parent)
        bw.setMaximumWidth(200)
        vbox = QVBoxLayout(bw)
        button = QPushButton("Plot Test")
        button.clicked.connect(self.plotTests)
        vbox.addWidget(button)
        button = QPushButton("Make Test Data")
        button.clicked.connect(self.tableTests)
        vbox.addWidget(button)
        button = QPushButton("Colormaps Demo")
        button.clicked.connect(self.colorMapDemo)
        vbox.addWidget(button)
        button = QPushButton("Random Format")
        button.clicked.connect(self.randomFormat)
        vbox.addWidget(button)
        return bw

    def plotTests(self):
        """Test general plotting"""

        self.table.selectAll()
        opts = self.table.pf.opts['general']
        for kind in ['line','area','scatter','histogram','boxplot','violinplot',
                    'heatmap','density']:
            opts.updateWidgets({'kind':kind,'subplots':'single'})
            self.table.plot()
            QtCore.QCoreApplication.processEvents()
            time.sleep(0.3)
            self.parent.plotToScratchpad(label=kind)
        for kind in ['bar','line','area','histogram']:
            opts.updateWidgets({'kind':kind,'axes_layout':'multiple'})
            self.table.plot()
            QtCore.QCoreApplication.processEvents()
            time.sleep(0.3)
            self.parent.plotToScratchpad(label=kind+'_subplots')
        self.parent.showScratchpad()
        return

    def colorMapDemo(self):

        opts = self.table.pf.opts['general']
        formatopts = self.table.pf.opts['format']
        labelopts = self.table.pf.opts['labels']
        self.table.selectAll()
        cmaps = sorted(m for m in plt.cm.datad if not m.endswith("_r"))
        for cmap in random.sample(cmaps,20):
            #opts.updateWidgets({'kind':'heatmap'})
            formatopts.updateWidgets({'colormap':cmap})
            labelopts.updateWidgets({'title':cmap})
            self.table.plot()
            QtCore.QCoreApplication.processEvents()
            time.sleep(0.3)
        return

    def randomFormat(self):
        """Random format settings"""

        for k in ['format','labels']:
            opts = self.table.pf.opts[k]
            opts.randomSettings()
            opts.updateWidgets()
        self.table.plot()
        return

    def tableTests(self):
        """Test table functions"""

        df = util.getSampleData(50,5)
        self.table.table.model.df = df
        self.table.refresh()
        return

    def quit(self, evt=None):
        """Override this to handle pane closing"""

        self.main.close()
        return

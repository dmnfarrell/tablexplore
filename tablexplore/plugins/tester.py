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
import pickle, gzip
from collections import OrderedDict
from tablexplore.qt import *
import pandas as pd
from tablexplore import util, data, core, dialogs
from tablexplore.plugin import Plugin

class ExamplePlugin(Plugin):
    """Template plugin for TableExplore"""

    #uncomment capabilities list to appear in menu
    capabilities = ['gui','docked']
    requires = ['']
    menuentry = 'Testing'

    def main(self, parent=None, table=None):
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

        if 'docked' in self.capabilities:
            self.mainwin = QDockWidget()
            self.mainwin.setFeatures(QDockWidget.DockWidgetClosable)
        else:
            self.mainwin = QWidget()
        self.frame = QWidget(self.mainwin)
        self.mainwin.setWidget(self.frame)
        layout =  QHBoxLayout()
        self.frame.setLayout(layout)
        #add table
        t = self.tablewidget = core.DataFrameWidget(self.frame, font=core.FONT,
                                    statusbar=False, toolbar=False)
        t.resize(500,500)
        layout.addWidget(self.tablewidget)
        bw = self.createButtons(self.frame)
        layout.addWidget(bw)
        return

    def createButtons(self, parent):

        bw = QWidget(parent)
        bw.setMaximumWidth(100)
        vbox = QVBoxLayout(bw)
        button = QPushButton("Plot Test")
        button.clicked.connect(self.plotTests)
        vbox.addWidget(button)
        button = QPushButton("Table Test")
        button.clicked.connect(self.tableTests)
        vbox.addWidget(button)
        button = QPushButton("Close")
        button.clicked.connect(self.quit)
        vbox.addWidget(button)
        return bw

    def plotTests(self):
        """Test plotting"""

        self.tablewidget.pf = self.table.pf
        df = data.getSampleData(100,4)
        self.tablewidget.table.model.df = df
        self.tablewidget.refresh()
        self.tablewidget.selectAll()
        opts = self.tablewidget.pf.generalopts
        for kind in ['line','area','scatter','histogram','boxplot','violinplot',
                    'heatmap','density']:
            opts.updateWidgets({'kind':kind})
            self.tablewidget.plot()
            QtCore.QCoreApplication.processEvents()
            time.sleep(0.3)
        opts.updateWidgets({'groupby':'label'})
        for kind in ['bar','line','area','histogram','heatmap']:
            #opts.updateWidgets({'kind':kind})
            self.tablewidget.plot()
            QtCore.QCoreApplication.processEvents()
            time.sleep(0.3)
        return

    def tableTests(self):
        """Test table functions"""

        df = data.getSampleData(500,5)
        self.tablewidget.table.model.df = df
        self.tablewidget.refresh()
        return

    def quit(self, evt=None):
        """Override this to handle pane closing"""

        self.mainwin.close()
        return

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
from tablexplore import util, core, dialogs
from tablexplore.plugin import Plugin

class ExamplePlugin(Plugin):
    """Template plugin for TableExplore"""

    #uncomment capabilities list to appear in menu
    capabilities = ['gui']
    requires = ['']
    menuentry = 'Example Plugin'
    name = 'Example Plugin'

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

        self.main = QWidget()

        layout = self.layout = QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.main.setLayout(layout)
        tb = self.textbox = dialogs.PlainTextEditor()
        tb.resize(300,300)
        layout.addWidget(tb)
        text = 'This is a sample plugin.\n'\
        'see https://github.com/dmnfarrell/tablexplore/tree/master/plugins '\
        'for code examples.'
        tb.insertPlainText(text)
        #add a table widget
        t = self.tablewidget = core.DataFrameWidget(self.main, font=core.FONT,
                                    statusbar=False, toolbar=False)
        t.resize(300,300)
        layout.addWidget(self.tablewidget)
        #add some buttons
        bw = self.createButtons(self.main)
        layout.addWidget(bw)
        return

    def createButtons(self, parent):

        bw = QWidget(parent)
        vbox = QVBoxLayout(bw)
        button = QPushButton("Close")
        button.clicked.connect(self.quit)
        vbox.addWidget(button)
        return bw

    def apply(self):
        """Run something"""

        return

    def quit(self, evt=None):
        """Override this to handle pane closing"""

        self.main.close()
        return

    def about(self):
        """About this plugin"""

        txt = "This plugin implements ...\n"+\
               "version: %s" %self.version
        return txt

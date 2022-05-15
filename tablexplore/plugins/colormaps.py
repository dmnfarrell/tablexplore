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
from matplotlib.colors import ListedColormap

class ColormapsPlugin(Plugin):
    """Template plugin for TableExplore"""

    #uncomment capabilities list to appear in menu
    capabilities = ['gui','docked']
    requires = ['']
    menuentry = 'Colormap Tool'
    iconfile = 'colormaps.png'
    name = 'Colormap Tool'

    def __init__(self, parent=None, table=None):
        """Customise this and/or doFrame for your widgets"""

        if parent==None:
            return
        self.parent = parent
        self.table = table
        #self.ID = 'Colormap Tool'
        self.createWidgets()
        return

    def _createMenuBar(self):
        """Create the menu bar for the application. """

        return

    def createWidgets(self):
        """Create widgets if GUI plugin"""

        self.main = QWidget()
        l = self.layout = QVBoxLayout()
        l.setSpacing(1)
        l.setAlignment(QtCore.Qt.AlignTop)
        self.main.setLayout(l)
        bw = self.createButtons(self.main)
        l.addWidget(bw)

        self.ncolors = w = QSpinBox()
        w.setValue(5)
        w.setRange(2,20)
        l.addWidget(w)
        self.cbw = QWidget()
        return

    def createButtons(self, parent):

        bw = QWidget(parent)
        bw.setMaximumWidth(200)
        vbox = QVBoxLayout(bw)
        button = QPushButton("Sample Colormaps")
        button.clicked.connect(self.showColorMaps)
        vbox.addWidget(button)
        button = QPushButton("Create Random")
        button.clicked.connect(self.makeRandom)
        vbox.addWidget(button)
        return bw

    def showColorMaps(self):

        cmaps = sorted(m for m in plt.cm.datad if not m.endswith("_r"))
        pf = self.table.pf
        n=20
        figsize = pf.getFigureSize()

        fig,ax=plt.subplots(n,1,figsize=figsize)
        axs=ax.flat
        for i in range(n):
            cmap = random.choice(cmaps)
            colors = util.gen_colors(cmap,10)
            util.show_colors(colors, ax=axs[i])
            axs[i].text(0.5, 0.5, cmap, horizontalalignment='center',
                    verticalalignment='center', transform=axs[i].transAxes)
        plt.tight_layout()
        pf.setFigure(fig)
        return

    def makeRandom(self):

        pf = self.table.pf
        figsize = pf.getFigureSize()
        fig = plt.figure(figsize=figsize)
        grid = fig.add_gridspec(4, 1, wspace=0.2, hspace=0.2)
        ax1=fig.add_subplot(grid[0, 0])
        n=int(self.ncolors.value())
        colors = util.random_colors(n=n,seed=None)
        util.show_colors(colors, ax=ax1)

        mycmap = ListedColormap(colors)

        X = util.getSampleData(1,cols=n).iloc[:,:-1]
        ax2=fig.add_subplot(grid[1:,0])
        #ax2.pcolor(X, cmap=mycmap)
        X.plot(kind='bar',cmap=mycmap,ax=ax2)
        pf.setFigure(fig)

        self.cbw.deleteLater()
        self.cbw = self.createColorButtons(self.main, colors)
        self.layout.addWidget(self.cbw)
        return

    def createColorButtons(self, parent, colors):

        bw = QWidget(parent)
        vbox = QVBoxLayout(bw)
        bw.setMaximumWidth(200)
        for c in colors:
            #r,g,b = util.hex_to_rgb(c)
            btn = dialogs.ColorButton()
            btn.setColor(c)
            vbox.addWidget(btn)

        return bw

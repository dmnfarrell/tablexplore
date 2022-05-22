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
import numpy as np
import pandas as pd
from tablexplore import util, core, dialogs
from tablexplore.plugin import Plugin
import matplotlib as mpl
import pylab as plt
from tablexplore import plotting

cmapsfile = core.cmapsfile

class ColormapsPlugin(Plugin):
    """Template plugin for TableExplore"""

    #uncomment capabilities list to appear in menu
    capabilities = ['gui']
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
        self.cbw = QWidget()
        return

    def createButtons(self, parent):

        bw = QWidget(parent)
        bw.setMaximumWidth(200)
        vbox = QVBoxLayout(bw)
        button = QPushButton("Sample Colormaps")
        button.clicked.connect(self.showColorMaps)
        vbox.addWidget(button)

        current = plotting.load_colormaps()
        self.current_w = cb = QComboBox()
        cb.addItems(['']+list(current.keys()))
        cb.currentIndexChanged.connect(self.loadCustom)
        vbox.addWidget(QLabel('load cmap colors:'))
        vbox.addWidget(cb)

        button = QPushButton("Random Colors")
        button.clicked.connect(self.makeRandom)
        vbox.addWidget(button)
        self.ncolors = w = QSpinBox()
        w.setValue(5)
        w.setRange(2,20)
        vbox.addWidget(QLabel('num colors:'))
        vbox.addWidget(w)

        vbox.addWidget(QLabel('type:'))
        self.cmaptype_w = cb = QComboBox()
        cb.addItems(['discrete','interpolated'])
        vbox.addWidget(cb)
        button = QPushButton("Update")
        button.clicked.connect(self.update)
        vbox.addWidget(button)
        button = QPushButton("Save")
        button.clicked.connect(self.save)
        vbox.addWidget(button)
        return bw

    def loadCustom(self):
        """Edit a saved cmap"""

        name = self.current_w.currentText()
        current = plotting.load_colormaps()
        cmap = current[name]
        try:
            clrs = cmap.__dict__['colors']
        except:
            clrs = []
        self.createColorButtons(clrs)
        return

    def showColorMaps(self):
        """Show sample colormaps"""
        
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
        """Create random colors"""

        n=int(self.ncolors.value())
        colors = self.colors = util.random_colors(n=n,seed=None)
        self.createColorButtons(colors)
        self.update()
        return

    def createColorButtons(self, colors):
        """Create buttons for color selection"""

        self.cbw.deleteLater()
        self.cbuttons = []
        self.cbw = QWidget(self.main)
        vbox = QVBoxLayout(self.cbw)
        self.cbw.setMaximumWidth(200)
        for c in colors:
            btn = dialogs.ColorButton()
            btn.setColor(c)
            vbox.addWidget(btn)
            self.cbuttons.append(btn)
        self.layout.addWidget(self.cbw)
        return

    def update(self, event=None):
        """Update the colormaps and previews"""

        colors = [btn._color for btn in self.cbuttons]
        type = self.cmaptype_w.currentText()

        if type == 'discrete':
            self.mycmap = mpl.colors.ListedColormap(colors)
        else:
            self.mycmap = get_continuous_cmap(colors)

        pf = self.table.pf
        figsize = pf.getFigureSize()
        fig = plt.figure(figsize=figsize)
        grid = fig.add_gridspec(5, 1, wspace=0.2, hspace=0.2)
        ax1=fig.add_subplot(grid[0, 0])

        util.show_colors(colors, ax=ax1)
        ax2 = fig.add_subplot(grid[1:,0])
        self.plot_examples(self.mycmap, ax2)
        pf.setFigure(fig)
        return

    def save(self):
        """Save colormap to file and register it"""

        current = plotting.load_colormaps()
        name, ok = QInputDialog.getText(self.main, 'Colormap name', 'Enter name:')
        if not ok:
            return
        #set name
        self.mycmap.name = name
        #register it
        mpl.colormaps.register(self.mycmap, force=True)
        #save as pickle
        current[name] = self.mycmap
        fp = open(cmapsfile, 'wb')
        pickle.dump(current, fp)
        fp.close()
        return

    def plot_examples(self, cmap, ax=None):
        """
        Helper function to plot data with associated colormap.
        """
        np.random.seed(19680801)
        data = np.random.randn(30, 30)
        psm = ax.pcolormesh(data, cmap=cmap, rasterized=True, vmin=-4, vmax=4)
        ax.figure.colorbar(psm, ax=ax)
        return

def get_continuous_cmap(hex_list):
    """
    https://towardsdatascience.com/beautiful-custom-colormaps-with-matplotlib-5bab3d1f0e72
    """

    #diverging
    #divnorm = mcolors.TwoSlopeNorm(vmin=z.min(),vcenter=center, vmax=z.max())

    rgb_list = [rgb_to_dec(hex_to_rgb(i)) for i in hex_list]
    float_list = list(np.linspace(0,1,len(rgb_list)))
    cdict = dict()
    for num, col in enumerate(['red', 'green', 'blue']):
        col_list = [[float_list[i], rgb_list[i][num], rgb_list[i][num]] for i in range(len(float_list))]
        cdict[col] = col_list
    cmp = mpl.colors.LinearSegmentedColormap('my_cmp', segmentdata=cdict, N=256)
    return cmp

def hex_to_rgb(value):
    '''
    Converts hex to rgb colours
    value: string of 6 characters representing a hex colour.
    Returns: list length 3 of RGB values'''
    value = value.strip("#") # removes hash symbol if present
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def rgb_to_dec(value):
    '''
    Converts rgb to decimal colours (i.e. divides each value by 256)
    value: list (length 3) of RGB values
    Returns: list (length 3) of decimal values'''
    return [v/256 for v in value]

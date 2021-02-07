"""
    Simple GIS plugin for tablexplore.
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
import random, string
from collections import OrderedDict
from tablexplore.qt import *
import pandas as pd
import numpy as np
from tablexplore import util, data, core, dialogs
from tablexplore.plugin import Plugin
import pylab as plt

# requires geopandas
import geopandas as gpd
import shapely
from shapely.geometry import Point, LineString, Polygon, MultiPolygon

homepath = os.path.expanduser("~")
qcolors = ['blue','green','crimson','blueviolet','brown','burlywood','cadetblue','chartreuse','chocolate',
            'coral','gold','cornflowerblue','cornsilk','khaki','orange','pink',
            'red','lime','mediumvioletred','navy','teal','darkblue','purple','orange',
            'marooon','salmon']
name = 'Simple GIS'


class Layer(object):
    def __init__(self, gdf, name, crs=None):
        self.gdf = gdf
        self.name = name
        self.crs = crs
        self.lw = 1
        self.ec = 'black'
        self.color = 'white'
        self.alpha = .9
        self.column_color = ''
        self.column_label = ''
        return

class GISPlugin(Plugin):
    """Geopandas map plotting plugin for TableExplore"""

    #uncomment capabilities list to appear in menu
    capabilities = ['gui','docked']
    requires = ['']
    menuentry = 'Simple GIS'
    iconfile = 'globe.png'

    def __init__(self, parent=None, table=None):
        """Customise this and/or doFrame for your widgets"""

        if parent==None:
            return
        self.parent = parent
        self.tablewidget = table
        self.ID = 'Simple GIS'
        self.layers = {}
        self.createWidgets()
        self.createMenu()
        return

    def createMenu(self):
        """Main menu"""

        self.menubar = QMenuBar(self.main)
        self.file_menu = QMenu('&File', self.main)
        self.file_menu.addAction('&Import', self.importFile)
        self.menubar.addMenu(self.file_menu)
        self.actions_menu = QMenu('&Actions', self.main)
        self.menubar.addMenu(self.actions_menu)
        self.about_menu = QMenu('&About', self.main)
        self.menubar.addMenu(self.about_menu)
        self.menubar.adjustSize()
        return

    def createWidgets(self):
        """Create widgets"""

        if 'docked' in self.capabilities:
            self.main = QDockWidget()
        else:
            self.main = QWidget()
        self.frame = QWidget(self.main)
        self.main.setWidget(self.frame)
        layout = self.layout = QHBoxLayout()
        self.frame.setLayout(layout)

        self.tree = QTreeWidget()
        self.tree.setHeaderItem(QTreeWidgetItem(["name","file"]))
        self.tree.setColumnWidth(0, 200)

        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)

        self.tree.customContextMenuRequested.connect(self.showTreeMenu)
        #self.tree.itemDoubleClicked.connect(handler)

        layout.addWidget(self.tree)
        #add some buttons
        bw = self.createButtons(self.frame)
        layout.addWidget(bw)
        return

    def createButtons(self, parent):
        """Buttons"""

        bw = QWidget(parent)
        vbox = QVBoxLayout(bw)
        button = QPushButton("Import shape file")
        button.clicked.connect(self.importFile)
        vbox.addWidget(button)
        button = QPushButton("Simulate Shapes")
        button.clicked.connect(self.simulateShapes)
        vbox.addWidget(button)
        button = QPushButton("Plot")
        button.clicked.connect(self.plot)
        vbox.addWidget(button)
        button = QPushButton("Close")
        button.clicked.connect(self.quit)
        vbox.addWidget(button)
        return bw

    def showTreeMenu(self, pos):
        """Show right cick tree menu"""

        item = self.tree.itemAt( pos )
        menu = QMenu(self.tree)
        editAction = menu.addAction("Edit Table")
        propsAction = menu.addAction("Properties")
        colorAction = menu.addAction("Set Color")
        deleteAction = menu.addAction("Delete")
        exportAction = menu.addAction("Export")
        action = menu.exec_(self.tree.mapToGlobal(pos))
        if action == editAction:
            self.edit(item)
        elif action == colorAction:
            self.setColor(item)
        elif action == propsAction:
            self.setProperties(item)
        elif action == deleteAction:
            self.delete(item)
        elif action == exportAction:
            self.export(item)
        return

    def importFile(self):
        """Import shapefile"""

        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self.main,"Save Project",
                                                  '.',"shapefile (*.shp);;All files (*.*)",
                                                  options=options)
        if not filename:
            return
        gdf = gpd.read_file(filename)
        name = os.path.basename(filename)
        self.addEntry(name, gdf)
        self.plot()
        return

    def addEntry(self, name, gdf):
        """Add geopandas dataframe entry to tree"""

        if name in self.layers:
            name = name+str(len(self.layers))
        item = QTreeWidgetItem(self.tree)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(0, Qt.Checked)
        item.setText(0, name)
        #add to layers
        new = Layer(gdf, name)
        self.layers[name] = new
        i = len(self.layers)
        clr = qcolors[i]
        new.color = clr
        item.setBackground(0 , QBrush(QColor(clr)))
        return

    def setColor(self, item):

        qcolor = QColorDialog.getColor()
        item.setBackground(0 , qcolor)
        name = item.text(0)
        self.layers[name].color = qcolor.name()
        return

    def plot(self):
        """Plot maps"""

        #get the plot frame from parent table widget
        pf = self.tablewidget.pf
        ax = pf.ax
        ax.clear()
        column=None
        for name in self.layers:
            layer = self.layers[name]
            clr = layer.color
            df = layer.gdf
            column = layer.column_color
            if layer.column_color != '':
                column=layer.column_color
                clr=None

            df.plot(ax=ax,column=column,color=clr,
                    ec=layer.ec,lw=layer.lw,alpha=layer.alpha)
            if layer.column_label != '':
                col = layer.column_label
                df.apply(lambda x: ax.annotate(text=x[col],
                    xy=x.geometry.centroid.coords[0], ha='right', fontsize=10),axis=1)

        pf.canvas.draw()
        plt.tight_layout()
        return

    def delete(self, item):
        """Remove layer"""

        name = item.text(0)
        del self.layers[name]
        self.tree.removeItemWidget(item, 0)
        return

    def edit(self, item):
        """edit dataframe in main table"""

        name = item.text(0)
        layer = self.layers[name]
        table = self.tablewidget.table
        table.model.df = layer.gdf
        table.refresh()
        return

    def setProperties(self, item):
        """Set selected item properties"""

        name = item.text(0)
        layer = self.layers[name]
        crs_vals = ['','EPSG:29990']
        cols = ['']+layer.gdf.columns
        opts = {'name':{'type':'entry','default':layer.name},
                'crs': {'type':'combobox','default':layer.crs,'items':crs_vals,'label':'CRS'},
                'linewidth': {'type':'spinbox','default':layer.lw,'range':(1,10)},
                'alpha': {'type':'spinbox','default':layer.alpha,'range':(0.1,1),'interval':0.1},
                'colorby': {'type':'combobox','default':layer.column_color,'items':cols,'label':'color by'},
                'labelby': {'type':'combobox','default':layer.column_label,'items':cols,'label':'labels'}
                }
        dlg = dialogs.MultipleInputDialog(self.main, opts, title='Layer Properties', width=200)
        dlg.exec_()
        if not dlg.accepted:
            return False

        layer.name = dlg.values['name']
        layer.lw = dlg.values['linewidth']
        layer.alpha = dlg.values['alpha']
        layer.column_color = dlg.values['colorby']
        layer.column_label = dlg.values['labelby']
        item.setText(0, name)
        self.plot()
        return

    def export(self, item):

        return

    def simulateShapes(self, n=5):
        """Make synthetic objects"""

        kinds = ['points','polygons']
        opts = {'name':{'type':'entry','default':'shape'},
                'kind':  {'type':'combobox','default':'polygons','items':kinds,'label':'Type'},
                'objects': {'type':'spinbox','default':3,'range':(1,500)},
                'sides': {'type':'spinbox','default':6,'range':(1,50)},
                }

        dlg = dialogs.MultipleInputDialog(self.main, opts, title='Make Shapes', width=200)
        dlg.exec_()
        if not dlg.accepted:
            return False
        name = dlg.values['name']
        n = dlg.values['objects']
        sides = dlg.values['sides']
        kind = dlg.values['kind']
        if kind == 'polygons':
            polygons = make_polygons(n, pts=sides)
            gdf = gpd.GeoDataFrame(geometry= gpd.GeoSeries(polygons))
        elif kind == 'points':
            points = make_points(n)
            gdf = gpd.GeoDataFrame(geometry= gpd.GeoSeries(points))
        gdf['label'] = random_labels(len(gdf))
        self.addEntry(name, gdf)
        self.plot()
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

def make_points(n=5, bounds=(1,1,50,50)):
    """Make points"""

    points = []
    minx, miny, maxx, maxy = bounds
    while len(points) < n:
        pnt = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        points.append(pnt)
    return points

def point_pos(x0, y0, d, theta):
    theta_rad = np.pi/2 - np.radians(theta)
    return x0 + d*np.cos(theta_rad), y0 + d*np.sin(theta_rad)

def make_polygons(n=5, pts=5, r=5, bounds=(1,1,50,50)):
    """Make polygons inside specific bounds"""

    centers = make_points(n, bounds)
    pts = random.randint(3,pts*2)
    polys = []
    for c in centers:
        poly = make_polygon(c.x,c.y,pts,r)
        polys.append(poly)
    return polys

def make_polygon(x=1,y=1,pts=10,r=5):
    """Make a single polygon"""

    coords = []
    angles = sorted(np.random.randint(0,360,pts))
    for i in angles:
        d = np.random.normal(r,r/10)
        x1,y1 = point_pos(x,y,d,i)
        coords.append((x1,y1))
    poly = Polygon(coords)
    return poly

def make_multipolygons(n=1):

    mpoly = MultiPolygon([self.make_polygon(i*np.random.randint(10),i*np.random.randint(10),
                        np.random.randint(5,10), 10) for i in range(n)])
    mpoly = shapely.ops.unary_union(mpoly)
    return mpoly

def random_labels(n):
    return [random_string(5) for i in range(n)]

def random_string(length):
    pool = string.ascii_letters + string.digits
    return ''.join(random.choice(pool) for i in range(length))

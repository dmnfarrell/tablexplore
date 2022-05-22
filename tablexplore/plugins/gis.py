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
from tablexplore import util, core, dialogs
from tablexplore.plugin import Plugin
import pylab as plt

# requires geopandas
import geopandas as gpd
import shapely
from shapely.geometry import Point, LineString, Polygon, MultiPolygon

homepath = os.path.expanduser("~")
qcolors = ['blue','green','crimson','lightblue','gold','burlywood','blueviolet','chartreuse',
            'cadetblue','coral','cornflowerblue','cornsilk','khaki','orange','pink','chocolate',
            'red','lime','mediumvioletred','navy','teal','darkblue','purple','orange',
            'salmon','brown']
version = 0.1

class Layer(object):
    def __init__(self, gdf, name, crs=None):
        self.gdf = gdf
        self.name = name
        self.filename = None
        self.crs = crs
        self.lw = 1
        self.color = 'white'
        self.ec = 'black'
        self.alpha = .7
        self.column_color = ''
        self.column_label = ''
        self.colormap = ''
        self.pointsize = 50
        self.labelsize = 10
        return

    def save(self):
        """Save if filename present"""

        if self.filename != None:
            self.gdf.to_file(filename)
        return

class GISPlugin(Plugin):
    """Geopandas map plotting plugin for TableExplore"""

    #uncomment capabilities list to appear in menu
    capabilities = ['gui','docked']
    requires = ['']
    version = 0.1
    menuentry = 'Simple GIS'
    iconfile = 'globe.png'
    name = 'Simple GIS'

    def __init__(self, parent=None, table=None):
        """Customise this and/or doFrame for your widgets"""

        if parent==None:
            return
        self.parent = parent
        self.tablewidget = table
        self.layers = {}
        self.createWidgets()
        self.createMenu()
        return

    def createMenu(self):
        """Main menu"""

        self.menubar = QMenuBar(self.main)
        self.file_menu = QMenu('File', self.main)
        self.file_menu.addAction('Import', self.importFile)
        self.file_menu.addAction('Import URL', self.importURL)
        self.file_menu.addAction('Load Test Map', self.loadTest)
        self.file_menu.addAction('Load World Map', self.loadWorldMap)
        self.menubar.addMenu(self.file_menu)
        self.layers_menu = QMenu('Layers', self.main)
        self.layers_menu.addAction('Clear', self.clear)
        self.menubar.addMenu(self.layers_menu)
        self.tools_menu = QMenu('Tools', self.main)
        self.tools_menu.addAction('Simulate Shapes', self.simulateShapes)
        self.geom_menu = QMenu('Geometry', self.tools_menu)
        self.geom_menu.addAction('Centroid', lambda: self.apply_geometry('centroid'))
        self.geom_menu.addAction('Boundary', lambda: self.apply_geometry('boundary'))
        self.geom_menu.addAction('Envelope', lambda: self.apply_geometry('envelope'))
        self.geom_menu.addAction('Convex hull', lambda: self.apply_geometry('convex_hull'))
        self.geom_menu.addAction('Buffer', lambda: self.apply_geometry('buffer'))
        self.geom_menu.addAction('Simplify', lambda: self.apply_geometry('simplify'))
        self.geom_menu.addAction('Merge Overlapping', self.mergeOverlap)
        self.tools_menu.addAction(self.geom_menu.menuAction())
        self.transform_menu = QMenu('Transform', self.tools_menu)
        self.transform_menu.addAction('Scale', lambda: self.apply_geometry('scale'))
        self.transform_menu.addAction('Rotate', lambda: self.apply_geometry('rotate'))
        self.transform_menu.addAction('Skew', lambda: self.apply_geometry('skew'))
        self.tools_menu.addAction(self.transform_menu.menuAction())
        self.set_menu = QMenu('Set', self.tools_menu)
        self.set_menu.addAction('Union', self.overlay)
        self.set_menu.addAction('Intersection', lambda: self.overlay('intersection'))
        self.set_menu.addAction('Difference', lambda: self.overlay('difference'))
        self.tools_menu.addAction(self.set_menu.menuAction())
        self.analysis_menu = QMenu('Analysis', self.tools_menu)
        self.tools_menu.addAction(self.analysis_menu.menuAction())
        self.analysis_menu.addAction('Distance Matrix', self.distanceMatrix)
        #self.analysis_menu.addAction('Nearest Neighbour', self.nearestNeighbour)
        self.menubar.addMenu(self.tools_menu)
        self.options_menu = QMenu('Options', self.main)
        self.subplotsaction = QAction('Multiple Subplots', self.options_menu, checkable=True)
        self.options_menu.addAction(self.subplotsaction)
        self.menubar.addMenu(self.options_menu)
        self.help_menu = QMenu('Help', self.main)
        self.menubar.addMenu(self.help_menu)
        self.help_menu.addAction('About', self.about)
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
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.showTreeMenu)
        #self.tree.itemDoubleClicked.connect(handler)
        self.tree.itemChanged.connect(self.itemClicked)
        layout.addWidget(self.tree)
        #add some buttons
        #bw = self.createToolBar(self.frame)
        self.toolbar = self.createToolBar(self.frame)
        layout.addWidget(self.toolbar)
        return

    def createToolBar(self, parent):
        items = {'plot': {'action':self.plot,'file':'plot-map'},
                 'moveup': {'action':lambda: self.moveLayer(1),'file':'arrow-up'},
                 'movedown': {'action':lambda: self.moveLayer(-1),'file':'arrow-down'},
                 'delete': {'action':self.delete,'file':'delete'},
                 }
        toolbar = QToolBar("Toolbar")
        toolbar.setOrientation(QtCore.Qt.Vertical)
        dialogs.addToolBarItems(toolbar, self.main, items)
        return toolbar

    def showTreeMenu(self, pos):
        """Show right cick tree menu"""

        item = self.tree.itemAt( pos )
        menu = QMenu(self.tree)
        editAction = menu.addAction("Edit Table")
        propsAction = menu.addAction("Properties")
        colorAction = menu.addAction("Set Color")
        deleteAction = menu.addAction("Delete")
        setfileAction = menu.addAction("Set File")
        action = menu.exec_(self.tree.mapToGlobal(pos))
        if action == editAction:
            self.edit(item)
        elif action == colorAction:
            self.setColor(item)
        elif action == propsAction:
            self.setProperties(item)
        elif action == deleteAction:
            self.delete(item)
        elif action == setfileAction:
            self.setFile(item)
        return

    def loadWorldMap(self):
        """Load a world map"""

        world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
        world = world[['continent', 'geometry']]
        self.addEntry('world',world)
        self.plot()
        return

    def loadTest(self):
        """Load a test map"""

        url = 'https://github.com/dmnfarrell/tablexplore/blob/master/data/zim_level2_districts.zip?raw=true'
        self.importShapefile(url)
        return

    def importShapefile(self, filename):

        ext = os.path.splitext(filename)[1]
        if ext == '.zip':
            filename = 'zip://'+filename
        gdf = gpd.read_file(filename)
        name = os.path.basename(filename)
        self.addEntry(name, gdf, filename)
        self.plot()
        return

    def importFile(self):
        """Import shapefile"""

        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self.main,"Import File",
                                                  '.',"shapefile (*.shp);;zip (*.zip);;All files (*.*)",
                                                  options=options)
        if not filename:
            return
        self.importShapefile(filename)
        return

    def importURL(self):

        opts = {'url':{'label':'Address','type':'entry','default':'',
                     'width':600 }}
        dlg = dialogs.MultipleInputDialog(self.main, opts, title='Import URL', width=600)
        dlg.exec_()
        if not dlg.accepted:
            return False
        url = dlg.values['url']
        self.importShapefile(url)
        return

    def setFile(self, item=None):
        """Attach a file to the layer"""

        if item is None:
            item = self.tree.selectedItems()[0]
        name = item.text(0)
        layer = self.layers[name]
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(self.main,"Save to File",
                                                  '.',"shapefile (*.shp);;All files (*.*)",
                                                  options=options)
        ext = os.path.splitext(filename)[1]
        if ext != '.shp':
            filename += '.shp'
        layer.gdf.to_file(filename)
        layer.filename = filename
        item.setText(1, filename)
        return

    def itemClicked(self, item, column):

        #if item.checkState(column) == Qt.Checked:
        #    self.replot()
        return

    def addEntry(self, name, gdf, filename=None):
        """Add geopandas dataframe entry to tree"""

        if name in self.layers:
            name = name+str(len(self.layers))
        item = QTreeWidgetItem(self.tree)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        item.setCheckState(0, QtCore.Qt.Checked)
        item.setText(0, name)
        item.setText(1, filename)
        #add to layers
        new = Layer(gdf, name)
        self.layers[name] = new
        new.filename = filename
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
        self.replot()
        return

    def plot(self, evt=None, ax=None, limits={}):
        """Plot maps"""

        subplots = self.subplotsaction.isChecked()
        order = self.getLayerOrder()
        checked = self.getChecked()
        #get the plot frame from parent table widget
        pf = self.tablewidget.pf
        column = None
        i=1
        pf.fig.clear()
        if ax == None:
            if subplots == 1:
                size = len(order)
                nrows = int(round(np.sqrt(size),0))
                ncols = int(np.ceil(size/nrows))
            else:
                ax = pf.fig.add_subplot(111)

        #pf.setStyle()
        #pf.applyPlotoptions()
        for name in order:
            if name not in checked:
                continue
            if subplots == 1:
                ax = pf.fig.add_subplot(nrows,ncols,i,label=name)
                ax.set_title(name)
            layer = self.layers[name]
            clr = layer.color
            df = layer.gdf
            column = layer.column_color
            cmap = layer.colormap
            if layer.column_color != '':
                column=layer.column_color
                df.plot(ax=ax,column=column,cmap=cmap,
                        ec=layer.ec,lw=layer.lw,alpha=layer.alpha)
            else:
                df.plot(ax=ax,color=clr,ec=layer.ec,lw=layer.lw,
                    markersize=layer.pointsize,alpha=layer.alpha)
            #labels
            if layer.column_label != '':
                col = layer.column_label
                df.apply(lambda x: ax.annotate(text=x[col],
                    xy=x.geometry.centroid.coords[0], ha='right', fontsize=layer.labelsize),axis=1)
            if name in limits:
                lims = limits[name]
                ax.set_xlim(lims[0])
                ax.set_ylim(lims[1])
            i+=1
            ax.id = name

        pf.canvas.draw()
        plt.tight_layout()
        return

    def getPlotLimits(self):

        pf = self.tablewidget.pf
        axes = pf.fig.axes
        limits = {}
        for ax in axes:
            limits[ax.id] = (ax.get_xlim(),ax.get_ylim())
        return limits

    def replot(self):
        """Plot after edits to layers"""

        lims = self.getPlotLimits()
        pf = self.tablewidget.pf
        self.plot(limits=lims)
        return

    def moveLayer(self, n=1):
        """Move layer up in tree"""

        l = self.tree.topLevelItemCount()
        item = self.tree.selectedItems()[0]
        row = self.tree.selectedIndexes()[0].row()
        name = item.text(0)
        if row-n >= l or row-n<0:
            return
        self.tree.takeTopLevelItem(row)
        self.tree.insertTopLevelItem(row - n, item)
        self.tree.setCurrentItem(item)
        return

    def getLayerOrder(self):

        order = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            order.append(item.text(0))
        return order[::-1]

    def getChecked(self):

        names=[]
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.checkState(0) == QtCore.Qt.CheckState.Checked:
                names.append(item.text(0))
        return names

    def clear(self):
        """Clear all layers"""

        reply = QMessageBox.question(self.main, 'Clear All',
                             'Are you sure?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return False
        self.layers = {}
        self.tree.clear()
        return

    def delete(self):
        """Remove layer"""

        item = self.tree.selectedItems()[0]
        row = self.tree.selectedIndexes()[0].row()
        name = item.text(0)
        del self.layers[name]
        self.tree.takeTopLevelItem(row)
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

        colormaps = sorted(m for m in plt.cm.datad if not m.endswith("_r"))
        name = item.text(0)
        layer = self.layers[name]
        crs_vals = ['','EPSG:29990']
        cols = ['']+list(layer.gdf.columns)
        cols.remove('geometry')
        clrs = ['black','white']+qcolors
        opts = {'name':{'type':'entry','default':layer.name},
                'crs': {'type':'combobox','default':layer.crs,'items':crs_vals,'label':'CRS'},
                'line width': {'type':'spinbox','default':layer.lw,'range':(0,15)},
                'edge color': {'type':'combobox','default':layer.ec,'items':clrs},
                'pointsize': {'type':'spinbox','default':layer.pointsize,'range':(50,500)},
                'alpha': {'type':'spinbox','default':layer.alpha,'range':(0.1,1),'interval':0.1},
                'colorby': {'type':'combobox','default':layer.column_color,'items':cols,
                'label':'color by'},
                'labelby': {'type':'combobox','default':layer.column_label,'items':cols,
                'label':'labels'},
                'labelsize':  {'type':'spinbox','default':layer.labelsize,'range':(5,40)},
                'cmap': {'type':'combobox','default':layer.colormap,'items':colormaps},
                }
        dlg = dialogs.MultipleInputDialog(self.main, opts, title='Layer Properties', width=200)
        dlg.exec_()
        if not dlg.accepted:
            return False

        layer.name = dlg.values['name']
        layer.lw = dlg.values['line width']
        layer.ec = dlg.values['edge color']
        layer.pointsize = dlg.values['pointsize']
        layer.alpha = dlg.values['alpha']
        layer.column_color = dlg.values['colorby']
        layer.column_label = dlg.values['labelby']
        layer.colormap = dlg.values['cmap']
        layer.labelsize = dlg.values['labelsize']
        item.setText(0, name)
        self.replot()
        return

    def export(self, item):

        return

    def overlay(self, how='union'):
        """Find difference"""

        items = self.tree.selectedItems()[:2]
        print (items)
        names = [i.text(0) for i in items]
        df1 = self.layers[names[0]].gdf
        df2 = self.layers[names[1]].gdf
        new = gpd.overlay(df1, df2, how=how)
        self.addEntry(names[0]+'_'+names[1]+'_'+how, new)
        self.replot()
        return

    def apply_geometry(self, func):
        """Apply function to geoseries"""

        params = {'buffer':
                  {'distance':{'type':'spinbox','default':0.1,'range':(1,100),'interval':0.1}},
                  'simplify':
                  {'tolerance':{'type':'spinbox','default':0.1,'range':(1,10),'interval':0.1}},
                  'scale':
                  {'xfact':{'type':'spinbox','default':0.1,'range':(1,10),'interval':0.1},
                   'yfact':{'type':'spinbox','default':0.1,'range':(1,10),'interval':0.1}},
                  'rotate':
                  {'angle':{'type':'spinbox','default':0.1,'range':(1,180),'interval':0.2}},
                  'skew':
                  {'xs':{'type':'spinbox','default':0.1,'range':(1,180),'interval':0.2},
                   'ys':{'type':'spinbox','default':0.1,'range':(1,180),'interval':0.2}, },
                 }
        if func in params:
            opts = params[func]
            dlg = dialogs.MultipleInputDialog(self.main, opts, title=func, width=200)
            dlg.exec_()
            if not dlg.accepted:
                return False

        item = self.tree.selectedItems()[0]
        name = item.text(0)
        layer = self.layers[name]
        if func in params:
            new = getattr(layer.gdf.geometry, func)(**dlg.values)
        else:
            new = getattr(layer.gdf.geometry, func)
        new = gpd.GeoDataFrame(geometry=new)
        self.addEntry(name+'_%s' %func, new)
        self.replot()
        return

    def mergeOverlap(self):

        item = self.tree.selectedItems()[0]
        name = item.text(0)
        layer = self.layers[name]
        new = merge_overlap(layer.gdf)
        self.addEntry(name+'_merged', new)
        return

    def distanceMatrix(self):
        """Get dist matrix"""

        item = self.tree.selectedItems()[0]
        name = item.text(0)
        layer = self.layers[name]

        cols = list(layer.gdf.columns)
        opts = {'index':{'type':'combobox','default':cols[0],'items':cols}}
        dlg = dialogs.MultipleInputDialog(self.main, opts, title='distance matrix', width=200)
        dlg.exec_()
        if not dlg.accepted:
            return False

        X = distance_matrix(layer.gdf, index=dlg.values['index'])
        table = self.tablewidget.table
        table.model.df = X
        table.refresh()
        return

    def nearestNeighbour(self):
        """get nearest neighbours"""

        item = self.tree.selectedItems()[0]
        name = item.text(0)
        layer = self.layers[name]
        cent = layer.gdf.centroid
        cent['nearest'] = cent.geometry.apply(lambda x: nearest(x, cent))

        from shapely.geometry import Point, LineString

        lines = cent.apply(lambda x: LineString((x.geometry,x.nearest)),1)
        new = gpd.GeoDataFrame(geometry=lines)
        self.addEntry(name+'_nn', new)
        return

    def simulateShapes(self, n=5):
        """Make synthetic objects"""

        kinds = ['points','polygons']
        opts = {'name':{'type':'entry','default':'shape'},
                'kind':  {'type':'combobox','default':'polygons','items':kinds,'label':'Type'},
                'objects': {'type':'spinbox','default':3,'range':(1,500)},
                'sides': {'type':'spinbox','default':6,'range':(1,50)},
                'size': {'type':'spinbox','default':.1,'range':(.01,1),'interval':0.01},
                'bounds':{'type':'entry','default':'0,0,50,50'},
                }

        dlg = dialogs.MultipleInputDialog(self.main, opts, title='Make Shapes', width=200)
        dlg.exec_()
        if not dlg.accepted:
            return False
        name = dlg.values['name']
        n = dlg.values['objects']
        sides = dlg.values['sides']
        kind = dlg.values['kind']
        bounds = dlg.values['bounds'].split(',')
        size = dlg.values['size']
        bounds = [int(i)for i in bounds]

        if kind == 'polygons':
            polygons = make_polygons(n, pts=sides, bounds=bounds, size=size)
            gdf = gpd.GeoDataFrame(geometry= gpd.GeoSeries(polygons))
            gdf = merge_overlap(gdf)
            gdf['area'] = gdf.geometry.area
        elif kind == 'points':
            points = make_points(n, bounds=bounds)
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

        text = "This plugin implements a simple GIS "+\
                "plugin with the ability to load and plot shapefiles. "+\
                "Version: %s" %version

        #icon = QIcon(os.path.join(core.pluginiconpath,self.iconfile))
        msg = QMessageBox.about(self.main, "About", text)
        return

# module level functions

def merge_overlap(gdf):
    """Merges overlapping polygons """

    intersection= gpd.overlay(gdf, gdf, how='intersection')
    union = intersection.unary_union
    shapes = gpd.GeoSeries([polygon for polygon in union])
    new = gpd.GeoDataFrame(geometry=shapes)
    return new

def nearest(point, gdf):
    gdf['dist'] = gdf.apply(lambda row:  point.distance(row.geometry),axis=1)
    return gdf.iloc[gdf['dist'].argmin()].geometry

def distance_matrix(gdf, index=None):
    """Distance matrix from points"""

    def distance(x,point):
        return x.distance(point)

    X=[]
    for i,r in gdf.iterrows():
        point = r.geometry
        x = gdf.geometry.apply(lambda x: round(distance(x,point),3))
        X.append(x)
    if index == None:
        index = gdf.index
    else:
        index = list(gdf[index])
    X = pd.DataFrame(X,index=index)#,columns=index)
    return X

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

def make_polygons(n=5, pts=5, bounds=(1,1,50,50), size=0.1):
    """Make polygons inside specific bounds"""

    centers = make_points(n, bounds)
    pts = random.randint(pts-2,pts+2)
    polys = []
    for c in centers:
        r = abs(bounds[2]-bounds[0])*size
        r = np.random.normal(r,r)
        poly = make_polygon(c.x,c.y,pts,r)
        polys.append(poly)
    return polys

def make_polygon(x=1,y=1,pts=10,r=5):
    """Make a single polygon"""

    coords = []
    angles = sorted(np.random.randint(0,360,pts))
    for i in angles:
        d = r/2
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

# -*- coding: utf-8 -*-

"""
    Implements core classes for tablexplore
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

import sys, os, io, platform
import tempfile
import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype as is_datetime
import string
from .qt import *

homepath = os.path.expanduser("~")
module_path = os.path.dirname(os.path.abspath(__file__))
iconpath = os.path.join(module_path, 'icons')
pluginiconpath = os.path.join(module_path, 'plugins', 'icons')
settingspath = os.path.join(homepath, '.config','tablexplore')
if not os.path.exists(settingspath):
    os.makedirs(settingspath)
cmapsfile = os.path.join(settingspath, 'cmaps.pkl')

textalignment = None
MODES = ['default','spreadsheet','locked']

if 'Windows' in platform.platform():
    defaultfont = 'Arial'
else:
    defaultfont = 'Monospace'
#default settings, used across modules
defaults = {
            'FONT' :defaultfont,
            'FONTSIZE' : 12,
            'ALIGNMENT' : 'w',
            'COLUMNWIDTH' : 80,
            'TIMEFORMAT' :'%m/%d/%Y',
            'PRECISION' :3,
            'SHOWPLOTTER' : True,
            'ICONSIZE' : 26,
            'PLOTSTYLE'  :'bmh',
            'DPI' : 100,
            'BGCOLOR' : '#F4F4F3',
            'THEME': 'Fusion'
}
#populate current class variable
for k in defaults:
    vars()[k] = defaults[k]

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
from . import dialogs, plotting, util

icons = {'load': 'open', 'save': 'export',
         'importexcel': 'excel',
         'copy': 'copy', 'paste': 'paste',
         'plot':'plot',
         'transpose':'transpose',
         'aggregate':'aggregate',
         'pivot': 'pivot',
         'melt':'melt', 'merge':'merge',
         'filter':'table-filter',
         'interpreter':'interpreter',
         'subtable':'subtable','clear':'clear'
         }

timeformats = ['infer','%d/%m/%Y','%d/%m/%y',
                '%Y/%m/%d','%y/%m/%d','%Y/%d/%m',
                '%d%m%Y','%Y%m%d','%Y%d%m',
                '%d-%b-%Y',
                '%Y-%m-%d %H:%M:%S','%Y-%m-%d %H:%M',
                '%d-%m-%Y %H:%M:%S','%d-%m-%Y %H:%M',
                '%Y','%m','%d','%b']

class ColumnHeader(QHeaderView):
    def __init__(self):
        super(QHeaderView, self).__init__()
        return

class RowHeader(QHeaderView):
    def __init__(self):
        super(QHeaderView, self).__init__()
        return

class SubWidget(QDockWidget):
    def __init__(self, parent, table):
        super(SubWidget, self).__init__(parent)
        self.table=table
        #self.setSizePolicy(QSizePolicy.Expanding , QSizePolicy.Expanding)
    def closeEvent(self, ce):
        self.table.showAll()
        #self.table.filtered = False
        self.table.model.highlighted = None
        self.table.refresh()
        #we should actually do this:
        #for i in xrange(self.layout.count()):
        #    item = self.layout.itemAt(i)
        #    widget = item.widget()
        #    widget.onClose()

class ItemEditorFactory(QItemEditorFactory):
    def __init__(self):
        super().__init__()

    def createEditor(self, userType, parent):
        #print (userType)
        #if userType == QVariant.Double:
        if userType == 6:
            doubleSpinBox = QDoubleSpinBox(parent)
            doubleSpinBox.setDecimals(5)
            doubleSpinBox.setMinimum(-1e6)
            return doubleSpinBox
        else:
            return super().createEditor(userType, parent)

class DataFrameWidget(QWidget):
    """Widget containing a tableview and toolbars"""
    def __init__(self, parent=None, dataframe=None, app=None,
                 toolbar=True, statusbar=True, **kwargs):

        super(DataFrameWidget, self).__init__()
        self.splitter = QSplitter(QtCore.Qt.Vertical, self)
        l = self.layout = QGridLayout()
        l.setSpacing(2)
        l.addWidget(self.splitter,1,1)
        self.table = DataFrameTable(self, dataframe, **kwargs)
        self.splitter.addWidget(self.table)
        self.splitter.setSizes((500,200))
        if toolbar == True:
            self.createToolbar()
        if statusbar == True:
            self.statusBar()
        self.pf = None
        self.app = app
        self.pyconsole = None
        self.subtabledock = None
        self.subtable = None
        self.filterdock = None
        self.finddock = None
        self.mode = 'default'
        self.table.model.dataChanged.connect(self.stateChanged)
        return

    #@Slot('QModelIndex','QModelIndex','int')
    def stateChanged(self, idx, idx2):
        """Run whenever table model is changed"""

        if hasattr(self, 'pf') and self.pf is not None:
            self.pf.updateData()

    def statusBar(self):
        """Status bar at bottom"""

        w = self.statusbar = QWidget(self)
        l = QHBoxLayout(w)
        w.setMaximumHeight(30)
        self.size_label = QLabel("")
        l.addWidget(self.size_label, 1)
        w.setStyleSheet('color: #1a216c; font-size:12px')
        self.layout.addWidget(w, 2, 1)
        self.updateStatusBar()
        return

    def createToolbar(self):
        """Create toolbar"""

        self.setLayout(self.layout)
        items = {'load': {'action': self.load,'file':'open'},
                 'importexcel': {'action':self.importExcel,'file':'excel'},
                 'copy': {'action':self.copy,'file':'copy','shortcut':'Ctrl+C'},
                 'paste': {'action':self.paste,'file':'paste','shortcut':'Ctrl+V'},
                 'insert': {'action':self.insert,'file':'table-insert'},
                 'plot': {'action':self.plot,'file':'plot'},
                 'transpose': {'action':self.transpose,'file':'transpose'},
                 'aggregate': {'action':self.aggregate,'file':'aggregate'},
                 'pivot': {'action':self.pivot,'file':'pivot'},
                 'melt': {'action':self.melt,'file':'melt'},
                 'merge': {'action':self.merge,'file':'merge'},
                 'filter':{'action':self.filter,'file':'table-filter'},
                 'interpreter': {'action':self.showInterpreter  ,'file':'interpreter'},
                 'subtable': {'action':self.subTableFromSelection,'file':'subtable'},
                 'clear': {'action':self.clear,'file':'clear'},
                 }

        self.toolbar = toolbar = QToolBar("Toolbar")
        toolbar.setIconSize(QtCore.QSize(ICONSIZE, ICONSIZE))
        toolbar.setOrientation(QtCore.Qt.Vertical)
        dialogs.addToolBarItems(toolbar, self, items)
        self.layout.addWidget(toolbar,1,2)
        return

    def applySettings(self, settings):
        """Settings"""

        #self.table.setFont(font)
        return

    def close(self):
        """Close events"""

        if self.pyconsole != None:
            self.pyconsole.closeEvent()
        return

    def refresh(self):

        self.table.refresh()
        return

    def updateStatusBar(self):
        """Update the table details in the status bar"""

        if not hasattr(self, 'size_label'):
            return
        df = self.table.model.df
        meminfo = self.table.getMemory()
        s = '{r} rows x {c} columns | {m}'.format(r=len(df), c=len(df.columns),m=meminfo)
        self.size_label.setText(s)
        return

    def load(self):
        return

    def save(self):
        return

    def getFileType(self):

        return ftype

    def importFile(self, filename=None, dialog=True, **kwargs):
        """Import csv file"""

        if filename == None:
            options = QFileDialog.Options()
            filename, _ = QFileDialog.getOpenFileName(self,"Import File",
                                 "","CSV files (*.csv);;Text Files (*.txt);;All Files (*)",
                                 options=options)
            if not filename:
                return

        if dialog is True:
            dlg = dialogs.ImportDialog(self, filename)
            dlg.exec_()
            if not dlg.accepted:
                return
            self.table.model.df = dlg.df
            self.refresh()
        else:
            self.table.model.df = pd.read_csv(filename)
            self.refresh()
        return

    def importPickle(self):

        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self,"Import Pickle",
                             "","pickle files (*.pkl *.pickle);;All Files (*)",
                             options=options)
        if filename:
            self.table.model.df = pd.read_pickle(filename)
            self.refresh()
        return

    def importExcel(self, filename=None):
        """Import excel file"""

        if filename == None:
            options = QFileDialog.Options()
            filename, _ = QFileDialog.getOpenFileName(self,"Import Excel",
                             "","xlsx files (*.xlsx);;xls Files (*.xls);;All Files (*)",
                             options=options)
        if filename:
            self.table.model.df = pd.read_excel(filename)
            self.refresh()
        return

    def importHDF(self):
        """Import hdf5 file"""

        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self,"Import Excel",
                             "","hdf files (*.hdf5);;All Files (*)",
                             options=options)
        if filename:
            self.table.model.df = pd.read_hdf(filename, **kwargs)
            self.refresh()
        return

    def importURL(self, recent):
        """Import hdf5 file"""

        delimiters = [',',r'\t',' ',';','/','&','|','^','+','-']
        opts = {'url':{'label':'Address','type':'combobox','default':'',
                     'items':recent, 'editable': True, 'width':600 },
                'sep':{'label':'Delimeter','type':'combobox','default':'',
                    'items':delimiters,'width':200}
                }
        dlg = dialogs.MultipleInputDialog(self, opts, title='Import URL', width=600)
        dlg.exec_()
        if not dlg.accepted:
            return False
        url = dlg.values['url']
        sep = dlg.values['sep']
        self.table.model.df = pd.read_csv(url, sep=sep)
        self.refresh()
        return url

    def exportTable(self):
        """Export table"""

        options = QFileDialog.Options()
        #options.setDefaultSuffix('csv')
        filename, _ = QFileDialog.getSaveFileName(self,"Export",
                             "","csv files (*.csv);;xlsx files (*.xlsx);;xls Files (*.xls);;All Files (*)",
                             options=options)
        if not filename:
            return
        df = self.table.model.df
        df.to_csv(filename)
        return

    def copy(self):
        """Copy to clipboard"""

        #check size of dataframe
        m = self.table.model.df.memory_usage(deep=True).sum()
        if m>1e8:
            answer = QMessageBox.question(self, 'Copy?',
                             'This data may be too large to copy. Are you sure?', QMessageBox.Yes, QMessageBox.No)
            if not answer:
                return
        df = self.table.getSelectedDataFrame()
        df.to_clipboard()
        return

    def paste(self):
        """Paste from clipboard"""

        self.table.storeCurrent()
        self.table.model.df = pd.read_clipboard(sep='\t', index_col=0)
                                #parse_dates=True, infer_datetime_format=True)
        self.refresh()
        return

    def insert(self):
        """Insert from clipboard"""

        self.table.storeCurrent()
        df = self.table.model.df
        new = pd.read_clipboard(sep='\t')
        self.table.model.df = pd.concat([df,new])
        self.refresh()
        return

    def addColumn(self):
        self.table.addColumn()

    def addRows(self):
        self.table.addRows()

    def plot(self):
        """Plot from selection"""

        if self.pf == None:
            self.createPlotViewer()
        self.pf.setVisible(True)
        df = self.getSelectedDataFrame()
        self.pf.replot(df)
        return

    def createPlotViewer(self, parent=None):
        """Create a plot widget attached to this table"""

        if self.pf == None:
            self.pf = plotting.PlotViewer(table=self.table, parent=parent)
            #self.table.selectionModel().selectionChanged.connect(self.pf.updateSeries)
        if parent == None:
            self.pf.show()
        return self.pf

    def info(self):
        """Table info"""

        buf = io.StringIO()
        self.table.model.df.info(verbose=True,buf=buf,memory_usage=True)
        td = dialogs.TextDialog(self, buf.getvalue(), 'Info', width=600, height=400)
        return

    def showAsText(self):
        """Show selection as text"""

        df = self.getSelectedDataFrame()
        dlg = dialogs.TextDialog(self, df.to_string(), width=800, height=400)
        dlg.exec_()
        return

    def clear(self):
        """Clear table"""

        self.table.storeCurrent()
        self.table.model.df = pd.DataFrame()
        self.refresh()
        return

    def findDuplicates(self):
        """Find or remove duplicates"""

        df = self.table.model.df
        cols = df.columns

        opts = {'remove':  {'type':'checkbox','default':0,'label':'Drop duplicates',
                'tooltip':'Remove duplicates'},
                'useselected':  {'type':'checkbox','default':0,'label':'Use selected columns' },
                'keep':{'label':'Keep','type':'combobox','default':'first',
                             'items':['first','last'], 'tooltip':'values to keep'},
                'inplace':{'type':'checkbox','default':0,'label':'In place' },
                }
        dlg = dialogs.MultipleInputDialog(self, opts, title='Clean Data')
        dlg.exec_()
        if not dlg.accepted:
            return
        kwds = dlg.values
        keep = kwds['keep']
        remove = kwds['remove']
        inplace = kwds['inplace']
        if kwds['useselected'] == 1:
            idx = self.table.getSelectedColumns()
            cols = df.columns[idx]
        else:
            cols = df.columns

        new = df[df.duplicated(subset=cols,keep=keep)]
        if remove == True:
            new = df.drop_duplicates(subset=cols,keep=keep)
            if inplace == True:
                self.table.model.df = new
                self.refresh()
            elif len(new)>0:
                self.showSubTable(new)
        else:
            self.showSubTable(new)
        return

    def manageColumns(self):
        """Edit columns"""

        df = self.table.model.df
        cols = df.columns
        dlg = dialogs.ManageColumnsDialog(self, df)
        dlg.exec_()
        if not dlg.accepted:
            return

    def cleanData(self):
        """Deal with missing data"""

        df = self.table.model.df
        cols = df.columns
        fillopts = ['fill scalar','','ffill','bfill','interpolate']
        opts = {'replace':{'label':'Replace','type':'entry','default':'',
                             'tooltip':'replace with'},
                'symbol':{'label':'Fill empty/replace with','type':'combobox','default':'',
                             'items':['',0,'null','-','x'], 'editable': True, 'tooltip':'seperator'},
                'method':{'label':'Fill missing method','type':'combobox','default':'',
                                     'items':fillopts, 'tooltip':''},
                'limit':  {'type':'checkbox','default':1,'label':'Limit gaps',
                                'tooltip':' '},
                'dropcols':  {'type':'checkbox','default':0,'label':'Drop columns with null data',
                                'tooltip':' '},
                'droprows':  {'type':'checkbox','default':0,'label':'Drop rows with null data',
                                'tooltip':' '},
                'how':{'label':'Drop method','type':'combobox','default':'',
                             'items':['any','all'], 'tooltip':''},
                'dropduplicatecols':  {'type':'checkbox','default':0,'label':'Drop duplicate columns',
                                'tooltip':' '},
                'dropduplicaterows':  {'type':'checkbox','default':0,'label':'Drop duplicate rows',
                                'tooltip':' '},
                'rounddecimals':  {'type':'spinbox','default':0,'label':'Round Numbers',
                                'tooltip':' '},
                }

        dlg = dialogs.MultipleInputDialog(self, opts, title='Clean Data')
        dlg.exec_()
        if not dlg.accepted:
            return
        kwds = dlg.values
        replace = kwds['replace']
        symbol = kwds['symbol']
        method = kwds['method']

        if symbol == 'null':
            symbol = np.nan
        try:
            replace = float(replace)
        except:
            pass
        if symbol != '':
            if replace != '':
                df = df.replace(to_replace=replace, value=symbol)
            else:
                df = df.fillna(symbol)
        if kwds['dropcols'] == 1:
            df = df.dropna(axis=1,how=kwds['how'])
        if kwds['droprows'] == 1:
            df = df.dropna(axis=0,how=kwds['how'])
        if method == '':
            pass
        elif method == 'fill scalar':
            df = df.fillna(kwds['symbol'])
        elif method == 'interpolate':
            df = df.interpolate()
        else:
            df = df.fillna(method=method, limit=kwds['limit'])
        if kwds['dropduplicaterows'] == 1:
            df = df.drop_duplicates()
        if kwds['dropduplicatecols'] == 1:
            df = df.loc[:,~df.columns.duplicated()]
        if kwds['rounddecimals'] != 0:
            df = df.round(rounddecimals)

        self.table.model.df = df
        #print (df)
        self.refresh()
        return

    def convertNumeric(self):
        """Convert cols to numeric if possible"""

        df = self.table.model.df
        idx = self.table.getSelectedColumns()

        types = ['float','int']
        opts = {'convert to':  {'type':'combobox','default':'int','items':types,'label':'Convert To',
                                        'tooltip':' '},
                'removetext':  {'type':'checkbox','default':1,'label':'Try to remove text',
                                                        'tooltip':' '},
                'convert currency':  {'type':'checkbox','default':1,'label':'Convert currency',
                                                        'tooltip':' '},
                'selected columns only':  {'type':'checkbox','default':0,'label':'Selected columns only',
                                                        'tooltip':' '},
                'fillempty':  {'type':'checkbox','default':0,'label':'Fill Empty',
                                                        'tooltip':' '},
               }
        dlg = dialogs.MultipleInputDialog(self, opts, title='Convert Numeric')
        dlg.exec_()
        if not dlg.accepted:
            return
        kwds = dlg.values
        convtype = kwds['convert to']
        currency = kwds['convert currency']
        removetext = kwds['removetext']
        useselected = kwds['selected columns only']
        fillempty = kwds['fillempty']

        if useselected == 1 and len(idx)>0:
            colnames = df.columns[idx]
        else:
            colnames = df.columns
        print (idx,colnames)
        self.table.storeCurrent()
        for c in colnames:
            x = df[c]
            if fillempty == 1 or convtype is int:
                x = x.fillna(0)
            if currency == 1:
                x = x.replace( '[\$\£\€,)]','', regex=True ).replace( '[(]','-', regex=True )
            if removetext == 1:
                x = x.replace( '[^\d.]+', '', regex=True)
            try:
                self.table.model.df[c] = pd.to_numeric(x, errors='coerce').astype(convtype)
            except:
                pass
        self.refresh()
        return

    def convertTypes(self):

        dlg = dialogs.ConvertTypesDialog(self, self.table.model.df)
        dlg.exec_()
        if not dlg.accepted:
            return
        return

    def convertColumnNames(self):
        """Reformat column names"""

        df = self.table.model.df
        opts = {'replace':  {'type':'entry','default':'','label':'Replace'},
                'with':  {'type':'entry','default':'','label':'With'},
                'prefix':  {'type':'entry','default':'','label':'Prefix'},
                'truncate':  {'type':'spinbox','default':0,'label':'Truncate',range:(0,100)},
                'convertcase':  {'type':'combobox','default':'','items':['','upper','lower','title'],
                'label':'Convert Case'}
               }

        dlg = dialogs.MultipleInputDialog(self, opts, title='Format Column Names', width=300)
        dlg.exec_()
        if not dlg.accepted:
            return
        kwds = dlg.values
        repl = kwds['replace']
        wth = kwds['with']
        trunc = kwds['truncate']
        convertcase = kwds['convertcase']
        self.table.storeCurrent()

        df = self.table.model.df
        if repl != '':
            df.columns = [i.replace(repl,wth) for i in df.columns]
        if kwds['prefix'] != '':
            df.columns = kwds['prefix'] + df.columns
        #if pattern != '':
        #    df.columns = [i.replace(pattern,repl) for i in df.columns]
        if convertcase == 'lower':
            df.columns = df.columns.str.lower()
        elif convertcase == 'upper':
            df.columns = df.columns.str.upper()
        elif convertcase == 'title':
            df.columns = df.columns.str.title()

        if trunc > 0:
            df.columns = [i[:trunc] for i in df.columns]
        self.refresh()
        return

    def applyColumnFunction(self, column):
        """Apply column wise functions, applies a calculation per row and
        ceates a new column."""

        df = self.table.model.df
        tablecols = ['']+list(df.columns)
        col = column
        idx = self.table.getSelectedColumns()
        cols = df.columns[idx]
        if len(cols) == 0:
            cols = [column]

        singlefuncs = ['divide','multiply','mod','add','round','floor','ceil','trunc',
                        'power','log','exp','log10','log2',
                        'negative','sign','diff',
                        'sin','cos','tan','degrees','radians']
        multifuncs = ['mean','std','max','min','sum']

        if len(cols)>1:
            funcs = multifuncs+singlefuncs
        else:
            funcs = singlefuncs
        types = ['float','int']
        opts = {'funcname':  {'type':'combobox','default':'int','items':funcs,'label':'Function'},
                'scalar': {'type':'entry','default':1,'label':'Argument'},
                'newcol':  {'type':'entry','default':'','items':funcs,'label':'New column name'},
                'inplace':  {'type':'checkbox','default':False,'label':'Update in place'},
                'suffix':  {'type':'entry','default':'_x','items':funcs,'label':'Suffix'},
                'group': {'type':'combobox','default':'','items':tablecols,'label':'Apply per Group'},
               }
        dlg = dialogs.MultipleInputDialog(self, opts, title='Apply Function', width=300)
        dlg.exec_()
        if not dlg.accepted:
            return
        kwds = dlg.values
        funcname = kwds['funcname']
        arg = kwds['scalar']
        newcol = kwds['newcol']
        inplace = kwds['inplace']
        suffix = kwds['suffix']
        group = kwds['group']

        if funcname == 'diff':
            func = funcname
        else:
            func = getattr(np, funcname)

        self.table.storeCurrent()

        if newcol == '':
            if len(cols)>3:
                s = ' %s cols' %len(cols)
            else:
                s =  '(%s)' %(','.join(cols))[:20]
            newcol = funcname + s

        if funcname == 'divide':
            result = df[cols] / float(arg)
        elif funcname == 'multiply':
            result = df[cols] * float(arg)
        elif funcname == 'mod':
            result = df[cols] % float(arg)
        elif funcname == 'add':
            result = df[cols] + float(arg)
        elif funcname == 'power':
            result = df[cols]**float(arg)
        elif len(cols) >= 2:
            result = df[cols].apply(func, 1)
        else:
            if inplace == True:
                newcol = col
            if group != '':
                result = df.groupby(group)[col].apply(func)
            else:
                result = df[col].apply(func, 1)

        if inplace == True or funcname in ['divide','mulitply','mod','add','power']:
            df[cols] = result
        else:
            idx = df.columns.get_loc(col)
            df.insert(idx+1, newcol, result)
        self.refresh()
        return

    def _getFunction(self, funcname, obj=None):
        """Get a function as attribute of a class by name"""

        if obj != None:
            func = getattr(obj, funcname)
            return func
        if hasattr(pd, funcname):
            func = getattr(pd, funcname)
        elif hasattr(np, funcname):
            func = getattr(np, funcname)
        else:
            return
        return func

    def applyTransformFunction(self, column):
        """Apply resampling and transform functions on a single column."""

        df = self.table.model.df
        col = column
        cols = [column]
        idx = self.table.getSelectedColumns()
        if len(idx)>1:
            cols = df.columns[idx]

        ops = ['rolling window','expanding','shift']
        winfuncs = ['sum','mean','std','max','min','sem','var','quantile']
        wintypes = ['','boxcar','triang','blackman','hamming','bartlett',
                    'parzen','bohman','blackmanharris','nuttall','barthann']
        opts = {'operation': {'type':'combobox','default':'int','items':ops,'label':'Operation'},
                'winfunc':  {'type':'combobox','default':'int','items':winfuncs,'label':'Function'},
                'window': {'type':'spinbox','default':1, 'label':'Window','range':(1,1000)},
                'periods': {'type':'spinbox','default':1, 'label':'Periods','range':(1,1000)},
                'wintype': {'type':'combobox','default':'','items':wintypes,'label':'Window type'},
                'center':  {'type':'checkbox','default':True,'label':'Center window'},
                'newcol':  {'type':'entry','default':'','label':'New column name'},
                'inplace':  {'type':'checkbox','default':False,'label':'Update in place'},
                'suffix':  {'type':'entry','default':'_x','label':'Suffix'}
               }

        dlg = dialogs.MultipleInputDialog(self, opts, title='Transform/Resample', width=300)
        dlg.exec_()
        if not dlg.accepted:
            return
        kwds = dlg.values

        self.table.storeCurrent()
        op = kwds['operation']
        winfunc = kwds['winfunc']
        wintype = kwds['wintype']
        window = kwds['window']
        periods = kwds['periods']
        suffix = kwds['suffix']
        inplace = kwds['inplace']
        newcol = kwds['newcol']
        center = kwds['center']

        if wintype == '':
            wintype=None

        for col in cols:
            if op == 'rolling window':
                w = df[col].rolling(window=window, win_type=wintype, center=center)
                func = self._getFunction(winfunc, obj=w)
                result = func()
            elif op == 'expanding':
                func = self._getFunction(winfunc)
                result = df[col].expanding(2, center=True).apply(func)
            elif op == 'shift':
                result = df[col].shift(periods=periods)

            if result is None:
                return
            if newcol == '' or len(cols)>1:
                newcol = winfunc+'('+str(col)+')'
            if inplace == True:
                df[col] = result
            else:
                if newcol in df.columns:
                    newcol = dialogs.getName(self, txt="Enter Column Name")
                idx = df.columns.get_loc(col)
                df.insert(idx+1, newcol, result)
        self.refresh()
        return

    def fillDates(self, column):
        """Fill with datetime"""

        df = self.table.model.df
        st='01/01/2022'
        en='02/01/2022'
        freqs = ['auto','M','W','D','H','min','S','Q','A','AS','L','U']
        opts = {
                'start':  {'type':'entry','default':st,'label':'Start','tooltip':'start value if filling with range'},
                'end':  {'type':'entry','default':en,'label':'End','tooltip':'end value if filling with range'},
                'freq': {'type':'combobox','default':'auto','items':freqs,'label':'Freq'}
                }
        dlg = dialogs.MultipleInputDialog(self, opts, title='Fill Dates', width=300)
        dlg.exec_()
        if not dlg.accepted:
            return
        kwds = dlg.values
        start = kwds['start']
        end = kwds['end']
        freq = kwds['freq']
        periods = None
        if freq == 'auto':
            freq=None
            periods = len(df)
        l=len(df)
        data = pd.date_range(start=start, end=end, freq=freq, periods=periods)[:l]
        #print (data)
        self.table.storeCurrent()
        self.table.model.df[column] = data
        self.refresh()
        return

    def fillStrings(self, column):
        """Fill column with string data"""

        df = self.table.model.df
        chartypes = ['lower','upper','printable']
        opts = {'length': {'type':'spinbox','default':5,'label':'Length'},
                'chartype':{'type':'combobox','items':chartypes,'default':'lower','label':'Word type'},
            }
        dlg = dialogs.MultipleInputDialog(self, opts, title='Fill String', width=300)
        dlg.exec_()
        if not dlg.accepted:
            return
        kwds = dlg.values
        namelen = kwds['length']
        chartype = kwds['chartype']
        if chartype == 'lower':
            data = [util.gen_lower(namelen) for i in range(len(df))]
        elif chartype == 'upper':
            data = [util.gen_upper(namelen) for i in range(len(df))]
        else:
            data = [util.gen_word(namelen) for i in range(len(df))]
        self.table.storeCurrent()
        self.table.model.df[column] = data
        self.refresh()

    def fillData(self, column):
        """Fill column with data"""

        dists = ['normal','gamma','uniform','random int','logistic']
        df = self.table.model.df
        opts = {'value': {'type':'entry','default':'','label':'Single Value'},
                'random':  {'type':'checkbox','default':0,'label':'Random Noise',
                                        'tooltip':' '},
                'dist':  {'type':'combobox','default':'int',
                    'items':dists,'label':'Distribution', 'tooltip':' '},
                'low':  {'type':'entry','default':0,'label':'Low','tooltip':'start value if filling with range'},
                'high':  {'type':'entry','default':1,'label':'High','tooltip':'end value if filling with range'},
                'mean':  {'type':'entry','default':1,'label':'Mean'},
                'std':  {'type':'entry','default':1,'label':'St. Dev'},
        }

        dlg = dialogs.MultipleInputDialog(self, opts, title='Fill', width=300)
        dlg.exec_()
        if not dlg.accepted:
            return
        kwds = dlg.values

        value = kwds['value']
        low = kwds['low']
        high = kwds['high']
        random = kwds['random']
        dist = kwds['dist']
        param1 = float(kwds['mean'])
        param2 = float(kwds['std'])

        if low != '' and high != '':
            try:
                low=float(low); high=float(high)
            except:
                logging.error("Exception occurred", exc_info=True)
                return
        if value != '':
            data = value
        elif random == True:
            if dist == 'normal':
                data = np.random.normal(param1, param2, len(df))
            elif dist == 'gamma':
                data = np.random.gamma(param1, param2, len(df))
            elif dist == 'uniform':
                data = np.random.uniform(low, high, len(df))
            elif dist == 'random integer':
                data = np.random.randint(low, high, len(df))
            elif dist == 'logistic':
                data = np.random.logistic(low, high, len(df))
        else:
            step = (high-low)/len(df)
            data = pd.Series(np.arange(low,high,step))

        self.table.storeCurrent()
        self.table.model.df[column] = data
        self.refresh()
        return

    def convertDates(self, column):
        """Convert single or multiple columns into datetime or extract features from
        datetime object.
        """

        df = self.table.model.df
        props = ['day','dayofweek','month','hour','minute','second','microsecond','year',
                 'dayofyear','weekofyear','quarter','days_in_month','is_leap_year']
        opts = {'format':  {'type':'combobox','default':'int','editable':True,
                            'items':timeformats,'label':'Conversion format'},
                'errors':{'type':'combobox','items':['ignore','coerce'],'default':'ignore','label':'Errors'},
                'prop':  {'type':'list','default':'int',
                        'items':props,'label':'Extract from datetime'} }

        dlg = dialogs.MultipleInputDialog(self, opts, title='Convert/Extract Dates')
        dlg.exec_()
        if not dlg.accepted:
            return
        kwds = dlg.values

        format = kwds['format']
        props = kwds['prop']
        errors = kwds['errors']
        infer=False
        if format == 'infer':
            format = None
            infer = True
        temp = df[column]
        self.table.storeCurrent()
        if temp.dtype != 'datetime64[ns]':
            temp = pd.to_datetime(temp, format=format, infer_datetime_format=infer,
                                errors=errors)

        if props != '' and len(props)>0:
            for prop in props:
                new = getattr(temp.dt, prop)
                try:
                    new = new.astype(int)
                except:
                    pass
                if prop in df.columns:
                    df.drop(columns=prop)
                idx = df.columns.get_loc(column)
                df.insert(idx+1, prop, new)
        else:
            self.table.model.df[column] = temp
        self.refresh()
        return

    def applyStringMethod(self, column):
        """Apply string operation to column(s)"""

        df = self.table.model.df
        #cols = self.getSelectedColumns()
        col = column
        funcs = ['','split','strip','lstrip','lower','upper','title','swapcase','len',
                 'slice','replace','concat']
        opts = {'function':  {'type':'combobox','default':'',
                            'items':funcs,'label':'Function'},
                'sep':  {'type':'entry','default':',', 'label':'Split separator'},
                'start':  {'type':'entry','default':0, 'label':'Slice start'},
                'end':  {'type':'entry','default':1, 'label':'Slice end'},
                'pat':  {'type':'entry','default':'', 'label':'Pattern'},
                'repl': {'type':'entry','default':'', 'label':'Replace with'},
                'inplace': {'type':'checkbox','default':False, 'label':'In place'},
               }
        dlg = dialogs.MultipleInputDialog(self, opts, title='String Operation', width=300)
        dlg.exec_()
        if not dlg.accepted:
            return
        kwds = dlg.values

        self.table.storeCurrent()
        func = kwds['function']
        sep = kwds['sep']
        start = int(kwds['start'])
        end = int(kwds['end'])
        pat = kwds['pat']
        repl = kwds['repl']
        inplace = kwds['inplace']
        x = None

        if func == 'split':
            new = df[col].str.split(sep).apply(pd.Series)
            new.columns = [col+'_'+str(i) for i in new.columns]
            self.table.model.df = pd.concat([df,new],1)
            self.refresh()
            return
        elif func == 'strip':
            x = df[col].str.strip()
        elif func == 'lstrip':
            x = df[col].str.lstrip(pat)
        elif func == 'upper':
            x = df[col].str.upper()
        elif func == 'lower':
            x = df[col].str.lower()
        elif func == 'title':
            x = df[col].str.title()
        elif func == 'swapcase':
            x = df[col].str.swapcase()
        elif func == 'len':
            x = df[col].str.len()
        elif func == 'slice':
            x = df[col].str.slice(start,end)
        elif func == 'replace':
            x = df[col].replace(pat, repl, regex=True)
        elif func == 'concat':
            x = df[col].str.cat(df[cols[1]].astype(str), sep=sep)
        if inplace == 0:
            newcol = col+'_'+func
        else:
            newcol = col
        if x is None:
            print ('no function selected')
            return
        if inplace == 0:
            if newcol in df.columns:
                df.drop(columns=newcol)
            idx = df.columns.get_loc(col)
            df.insert(idx+1, newcol, x)
        self.refresh()
        return

    def resample(self):
        """Table time series resampling dialog. Should set a datetime index first."""

        df = self.table.model.df
        if not isinstance(df.index, pd.DatetimeIndex):
            msg = QMessageBox(None, "No datetime index",'Your date/time column should be the index.')
            msg.exec_()
            return

        conv = ['start','end']
        freqs = ['M','W','D','H','min','S','Q','A','AS','L','U']
        funcs = ['mean','sum','count','max','min','std','first','last']

        opts = {'freq':  {'type':'combobox','default':'M',
                            'items':freqs,'label':'Frequency'},
                'period':  {'type':'entry','default':1,
                            'label':'Period'},
                'func':  {'type':'combobox','default':'mean',
                        'items':funcs,'label':'Function'} }

        dlg = dialogs.MultipleInputDialog(self, opts, title='Resample', width=300)
        dlg.exec_()
        if not dlg.accepted:
            return
        kwds = dlg.values

        freq = kwds['freq']
        period = kwds['period']
        func = kwds['func']

        rule = str(period)+freq
        new = df.resample(rule).apply(func)
        self.showSubTable(new, index=True)
        return

    def merge(self):

        dlg = dialogs.MergeDialog(self, self.table.model.df)
        dlg.exec_()
        if not dlg.accepted:
            return
        return

    '''def runLastAction(self):
        """Run previous action again"""

        func = getattr(self, self.action['name'])
        print (func)
        func()
        return

    def storeAction(self, name):
        """Save last run action"""

        self.action = {'name':name}
        return'''

    def transpose(self):

        self.table.model.df = self.table.model.df.T
        self.refresh()
        return

    def pivot(self):
        """Pivot table"""

        dlg = dialogs.PivotDialog(self, self.table.model.df)
        dlg.exec_()
        if not dlg.accepted:
            return
        return

    def aggregate(self):
        """Groupby aggregate operation"""

        dlg = dialogs.AggregateDialog(self, self.table.model.df)
        dlg.exec_()
        if not dlg.accepted:
            return

    def melt(self):
        """Melt table"""

        dlg = dialogs.MeltDialog(self, self.table.model.df)
        dlg.exec_()
        if not dlg.accepted:
            return
        return

    def bin(self):
        """Split into bins using cut"""

        df = self.table.model.df
        new = pd.cut(df, bins, labels)
        return

    def filter(self):
        """Show filter dialog"""

        if self.filterdock == None:
            dock = self.filterdock = dock = SubWidget(self.splitter, self.table)
            dock.setFeatures(QDockWidget.DockWidgetClosable)
            self.splitter.setSizes((500,200))
            index = self.splitter.indexOf(dock)
            self.splitter.setCollapsible(index, False)
            self.filterdialog = dlg = dialogs.FilterDialog(dock, self.table, app=self.app)
            dock.setWidget(dlg)
        else:
            self.filterdock.show()
            self.splitter.setSizes((500,200))
            self.filterdialog.update()
        return

    def findreplace(self):
        """Find/replace dialog"""

        if self.finddock == None:
            dock = self.finddock = dock = SubWidget(self.splitter, self.table)
            dock.setFeatures(QDockWidget.DockWidgetClosable)
            self.splitter.setSizes((500,200))
            index = self.splitter.indexOf(dock)
            self.splitter.setCollapsible(index, False)
            self.finddialog = dlg = dialogs.FindReplaceDialog(dock, self.table, app=self.app)
            dock.setWidget(dlg)
        else:
            self.finddock.show()
            self.splitter.setSizes((500,200))
            self.finddialog.update()

        return

    def selectAll(self):
        """Select all data"""

        self.table.selectAll()
        return

    def getSelectedDataFrame(self):
        """Get selection as a dataframe"""

        return self.table.getSelectedDataFrame()

    def subTableFromSelection(self):

        df = self.getSelectedDataFrame()
        self.showSubTable(df)
        return

    def showSubTable(self, df=None, title=None, index=False, out=False):
        """Add the child table"""

        self.closeSubtable()
        if self.subtabledock == None:
            self.subtabledock = dock = QDockWidget(self.splitter)
            dock.setFeatures(QDockWidget.DockWidgetClosable)
            index = self.splitter.indexOf(dock)
            self.splitter.setCollapsible(index, False)
            self.splitter.addWidget(dock)
            self.splitter.setSizes((500,200))

        self.subtabledock.show()
        newtable = SubTableWidget(self.subtabledock, dataframe=df, statusbar=False, font=FONT)
        self.subtabledock.setWidget(newtable)
        self.subtable = newtable

        if hasattr(self, 'pf'):
            newtable.pf = self.pf
        #if index == True:
        #    newtable.showIndex()
        return

    def closeSubtable(self):

        if hasattr(self, 'subtable'):
            #w = self.splitter.widget(1)
            #w.deleteLater()
            self.subtable = None
        return

    def editMode(self, evt=None):
        """Change table edit mode"""

        index = self.sender().data()
        mode = MODES[index]
        if mode == 'default':
            self.table.setEditTriggers(QAbstractItemView.DoubleClicked)
        elif mode == 'spreadsheet':
            self.table.setEditTriggers(QAbstractItemView.AllEditTriggers)
        else:
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.mode = mode
        return

    def runScript(self):
        """Run a set of python commands on the table"""

        script = ['df = df[:10]']

        return

    def showInterpreter(self):
        """Show the Python interpreter"""

        if self.pyconsole == None:
            from . import interpreter
            self.consoledock = dock = QDockWidget(self.splitter)
            dock.setFeatures(QDockWidget.DockWidgetClosable)
            dock.resize(200,100)
            index = self.splitter.indexOf(dock)
            self.splitter.setCollapsible(index, False)
            self.pyconsole = interpreter.TerminalPython(dock, table=self.table, app=self.app)
            dock.setWidget(self.pyconsole)
            self.splitter.setSizes((500,300))
        else:
            self.consoledock.show()
        return

class HeaderProxyStyle(QProxyStyle):
    def drawControl(self, element, option, painter, widget=None):
        if element == QStyle.CE_Header:
            option.state &= ~QStyle.State_On
            option.state &= ~QStyle.State_Sunken
        super(HeaderProxyStyle, self).drawControl(
            element, option, painter, widget
        )

class HeaderView(QHeaderView):
    """"
    Column header class.
    """
    def __init__(self, parent):
        super(HeaderView, self).__init__(QtCore.Qt.Horizontal, parent)
        '''self.setStyleSheet(
            "QHeaderView::section{background-color: #ffffff; "
            "font-weight: bold; "
            "border-bottom: 1px solid gray;}")'''

        self.setDefaultAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.Alignment(QtCore.Qt.TextWordWrap))
        sizePol = QSizePolicy()
        sizePol.setVerticalPolicy(QSizePolicy.Maximum)
        sizePol.setHorizontalPolicy(QSizePolicy.Maximum)
        self.setSizePolicy(sizePol)
        self.MAX_HEIGHT = 240
        self.setMinimumHeight(26)
        self.setMaximumHeight(self.MAX_HEIGHT )
        self.setSectionsClickable(True)
        self.setSelectionBehavior(QTableView.SelectColumns)
        self.setStretchLastSection(False)
        return

    def sectionSizeFromContents(self, logicalIndex):
        """Get section size from contents"""

        text = self.model().headerData(logicalIndex, self.orientation(), QtCore.Qt.DisplayRole)
        alignment = self.defaultAlignment()
        metrics = QFontMetrics(self.fontMetrics())
        width = metrics.boundingRect(QtCore.QRect(), alignment, text).width()

        heights = []
        for i in range(self.count()):
            text = self.model().headerData(i, self.orientation(),QtCore.Qt.DisplayRole)
            size = self.sectionSize(i)
            rect = QtCore.QRect(0, 0, size, self.MAX_HEIGHT)
            heights.append(metrics.boundingRect(rect, alignment, text).height())
        height = sorted(heights)[-1] + 5
        return QtCore.QSize(width, height)

class DataFrameTable(QTableView):
    """
    QTableView with pandas DataFrame as model.
    """
    def __init__(self, parent=None, dataframe=None, font='Arial',
                    fontsize=12, columnwidth=80, timeformat='%m-%d-%Y',
                    bg='#F4F4F3', **kwargs):

        QTableView.__init__(self)
        self.parent = parent
        self.font = font
        self.fontsize = fontsize
        self.columnwidth = columnwidth
        self.timeformat = timeformat
        self.clicked.connect(self.showSelection)
        #self.doubleClicked.connect(self.handleDoubleClick)

        vh = self.verticalHeader()
        vh.setVisible(True)
        vh.setDefaultSectionSize(30)
        vh.setMinimumWidth(50)
        vh.setMaximumWidth(500)
        vh.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        vh.customContextMenuRequested.connect(self.rowHeaderMenu)

        self.headerview = HeaderView(self)
        self.setHorizontalHeader(self.headerview)
        hh = self.horizontalHeader()

        hh.setDefaultSectionSize(columnwidth)
        hh.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        hh.customContextMenuRequested.connect(self.columnHeaderMenu)
        hh.sectionPressed.connect(self.columnClicked)
        #hh.sectionPressed.disconnect()
        hh.setSectionsMovable(True)
        hh.setSelectionBehavior(QTableView.SelectColumns)
        hh.setSelectionMode(QAbstractItemView.ExtendedSelection)
        hh.setDefaultAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.Alignment(QtCore.Qt.TextWordWrap))

        #formats
        self.setDragEnabled(True)
        self.viewport().setAcceptDrops(True)

        #self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDropIndicatorShown(True)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.setCornerButtonEnabled(True)
        #self.setSortingEnabled(True)
        self.updateFont()

        #wrapping
        #self.setWordWrap(True)
        #self.resizeRowsToContents()

        tm = DataFrameModel(dataframe)
        self.setModel(tm)
        tm.bg = bg
        self.model = tm
        self.filtered = False
        self.setWordWrap(True)

        df = self.model.df
        #disable column dragging for large tables
        if len(df) > 1e5:
            #print (len(df))
            #hh.setHighlightSections(False)
            hh.setSectionsClickable(False)
            #hh.setStyle(HeaderProxyStyle())

        styledItemDelegate = QStyledItemDelegate()
        styledItemDelegate.setItemEditorFactory(ItemEditorFactory())
        self.setItemDelegate(styledItemDelegate)

        #temp file for undo
        file, self.undo_file = tempfile.mkstemp(suffix='.pkl')
        try:
            os.remove(self.undo_file)
        except:
            pass
        return

    def updateFont(self):
        """Update the font"""

        font = QFont(self.font)
        font.setPointSize(int(self.fontsize))
        self.setFont(font)
        self.horizontalHeader().setFont(font)
        self.verticalHeader().setFont(font)
        return

    def refresh(self):
        """Refresh table if dataframe is changed"""

        self.updateFont()
        #self.horizontalHeader().setDefaultSectionSize(COLUMNWIDTH)
        self.model.beginResetModel()
        index = self.model.index
        try:
            self.model.dataChanged.emit(0,0)
        except:
            self.model.dataChanged.emit(index(0,0),index(0,0))
        self.model.endResetModel()
        if hasattr(self.parent,'statusbar'):
            self.parent.updateStatusBar()
        return

    def showAll(self):
        """Re-show unfiltered"""

        if hasattr(self, 'dataframe') and self.dataframe is not None:
            self.model.df = self.dataframe
        self.filtered = False
        self.refresh()
        return

    def storeCurrent(self):
        """Store current version of the table before a major change is made"""

        self.prevdf = self.model.df#.copy()
        self.prevdf.to_pickle(self.undo_file)
        #self.parent.updatesignal.speak.emit()
        return

    def undo(self):
        """Undo last change to table"""

        if os.path.exists(self.undo_file):
            print ('undo-ing')
            self.model.df = pd.read_pickle(self.undo_file)
            self.refresh()
            os.remove(self.undo_file)
        return

    def getMemory(self):
        """Get memory info as string"""

        m = self.model.df.memory_usage(deep=True).sum()
        if m>1e5:
            m = round(m/1048576,2)
            units='MB'
        else:
            units='Bytes'
        s = "%s %s" %(m,units)
        return s

    def memory_usage(self):

        info = self.getMemory()
        msg = QMessageBox()
        msg.setText('Memory: '+info)
        msg.setWindowTitle('Memory Usage')
        msg.exec_()
        return

    def showSelection(self, item):

        cellContent = item.data()
        row = item.row()
        model = item.model()
        columnsTotal= model.columnCount(None)
        return

    def getColumnOrder(self):
        """Get column names from header in their displayed order"""

        hh = self.horizontalHeader()
        df = self.model.df
        logidx = [hh.logicalIndex(i) for i in range(0,self.model.columnCount())]
        cols = [df.columns[i] for i in logidx]
        return cols

    def checkColumnsUnique(self):
        """Check if columns are all unique"""

        df = self.model.df
        return len(df.columns) == len(set(df.columns))

    def getSelectedRows(self):

        sm = self.selectionModel()
        rows = [(i.row()) for i in sm.selectedIndexes()]
        rows = list(dict.fromkeys(rows).keys())
        return rows

    def getSelectedColumns(self):
        """Get selected column indexes"""

        sm = self.selectionModel()
        cols = [(i.column()) for i in sm.selectedIndexes()]
        cols = list(dict.fromkeys(cols).keys())
        return cols

    def getSelectedDataFrame(self):
        """Get selection as a dataframe"""

        df = self.model.df
        sm = self.selectionModel()
        rows = [(i.row()) for i in sm.selectedIndexes()]
        cols = [(i.column()) for i in sm.selectedIndexes()]
        #get unique rows/cols keeping order
        rows = list(dict.fromkeys(rows).keys())
        cols = list(dict.fromkeys(cols).keys())
        data = df.iloc[rows,cols]
        #try to get numeric data for plotting
        colnames = data.columns
        #for c in colnames:
        #try to get numeric values for plotting
        for c in range(len(data.columns)):
            #print (data.iloc[:,c])
            x = pd.to_numeric(data.iloc[:,c], errors='coerce').astype(float)
            if x.isnull().all():
                continue
            #data[c] = x
            data.iloc[:,c] = x
        return data

    def setSelected(self, rows, cols):
        """
        Set selection programmatically from a list of rows and cols.
        https://doc.qt.io/archives/qtjambi-4.5.2_01/com/trolltech/qt/model-view-selection.html
        """

        #print (rows,cols)
        if len(rows)==0 or len(cols)==0:
            return
        topleft = self.model.index(rows[0], cols[0])
        bottomright = self.model.index(rows[-1], cols[-1])
        selection = QtCore.QItemSelection(topleft, bottomright)
        mode = QtCore.QItemSelectionModel.Select
        self.selectionModel().select(selection, mode)
        return

    def getScrollPosition(self):
        """Get current row/col position"""

        hb = self.horizontalScrollBar()
        vb = self.verticalScrollBar()
        return vb.value(),hb.value()

    def setScrollPosition(self, row, col):
        """Move to row/col position"""

        idx = self.model.index(row, col)
        self.scrollTo(idx)
        return

    def handleDoubleClick(self, item):

        cellContent = item.data()
        return

    def columnClicked(self, col):

        hheader = self.horizontalHeader()
        df = self.model.df
        #print (df[:2])
        #self.model.df = df.sort_values(df.columns[col])
        return

    def selectColumn(self, event):
        print (self.model.df)

    def sort(self, idx, ascending=True):
        """Sort by selected columns"""

        df = self.model.df
        sel = self.getSelectedColumns()
        if len(sel)>1:
            for i in sel:
                self.model.sort(i, ascending)
        else:
            self.model.sort(idx, ascending)
        return

    def deleteCells(self, rows, cols, answer=None):
        """Clear the cell contents"""

        if answer == None:
            answer = QMessageBox.question(self, 'Delete Cells?',
                             'Are you sure?', QMessageBox.Yes, QMessageBox.No)
        if not answer:
            return
        self.storeCurrent()
        #print (rows, cols)
        self.model.df.iloc[rows,cols] = np.nan
        return

    def setRowColor(self, rowIndex, color):
        for j in range(self.columnCount()):
            self.item(rowIndex, j).setBackground(color)

    def rowHeaderMenu(self, pos):
        """Row header popup menu"""

        vheader = self.verticalHeader()
        idx = vheader.logicalIndexAt(pos)
        menu = QMenu(self)

        resetIndexAction = menu.addAction("Reset Index")
        sortIndexAction = menu.addAction("Sort By Index \u2193")
        sortIndexDescAction = menu.addAction("Sort By Index \u2191")
        setTypeAction = menu.addAction("Set Type")
        deleteAction = menu.addAction("Delete Rows")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == resetIndexAction:
            self.resetIndex()
        elif action == sortIndexAction:
            self.sortIndex()
        elif action == sortIndexDescAction:
            self.sortIndex(ascending=False)
        elif action == setTypeAction:
            self.setIndexType()
        elif action == deleteAction:
            self.deleteRows()
        return

    def columnHeaderMenu(self, pos):
        """Column header right click popup menu"""

        hheader = self.horizontalHeader()
        idx = hheader.logicalIndexAt(pos)
        column = self.model.df.columns[idx]
        #model = self.model
        menu = QMenu(self)

        sortAction = menu.addAction("Sort \u2193")
        sortDescAction = menu.addAction("Sort \u2191")
        iconw = QIcon.fromTheme("open")
        sortAction.setIcon(iconw)
        setIndexAction = menu.addAction("Set as Index")

        colmenu = QMenu("Column",menu)
        deleteColumnAction = colmenu.addAction("Delete Column")
        renameColumnAction = colmenu.addAction("Rename Column")
        addColumnAction = colmenu.addAction("Add Column")
        setTypeAction = colmenu.addAction("Set Data Type")
        convertNumericAction = colmenu.addAction("Convert to Numeric")
        menu.addAction(colmenu.menuAction())

        fillmenu = QMenu("Fill",menu)
        filldataAction = fillmenu.addAction("Fill Data")
        fillstringsAction = fillmenu.addAction("Fill Strings")
        filldatesAction = fillmenu.addAction("Fill Dates")
        menu.addAction(fillmenu.menuAction())

        applyFunctionAction = menu.addAction("Apply Function")
        transformResampleAction = menu.addAction("Transform/Resample")
        stringOpAction = menu.addAction("String Operation")
        datetimeAction = menu.addAction("Date/Time Conversion")

        #sortAction = menu.addAction("Sort By")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == sortAction:
            self.sort(idx)
        elif action == sortDescAction:
            self.sort(idx, ascending=False)
        elif action == deleteColumnAction:
            self.deleteColumn(column)
        elif action == renameColumnAction:
            self.renameColumn(column)
        elif action == addColumnAction:
            self.addColumn()
        elif action == setTypeAction:
            self.setColumnType(column)
        elif action == convertNumericAction:
            self.parent.convertNumeric()
        elif action == setIndexAction:
            self.setIndex(column)
        elif action == datetimeAction:
            self.parent.convertDates(column)
        elif action == filldataAction:
            self.parent.fillData(column)
        elif action == fillstringsAction:
            self.parent.fillStrings(column)
        elif action == filldatesAction:
            self.parent.fillDates(column)
        elif action == applyFunctionAction:
            self.parent.applyColumnFunction(column)
        elif action == transformResampleAction:
            self.parent.applyTransformFunction(column)
        elif action == stringOpAction:
            self.parent.applyStringMethod(column)
        return

    def keyPressEvent(self, event):

        rows = self.getSelectedRows()
        cols = self.getSelectedColumns()
        if event.key() == QtCore.Qt.Key_Delete:
            self.deleteCells(rows, cols)

    def contextMenuEvent(self, event):
        """Reimplemented to create context menus for cells and empty space."""

        # Determine the logical indices of the cell where click occured
        hheader, vheader = self.horizontalHeader(), self.verticalHeader()
        position = event.globalPos()
        row = vheader.logicalIndexAt(vheader.mapFromGlobal(position))
        column = hheader.logicalIndexAt(hheader.mapFromGlobal(position))

        # Map the logical row index to a real index for the source model
        df = self.model.df
        if len(df) > 1:
            row = df.iloc[row]
        else:
            row = None
        # Show a context menu for empty space at bottom of table...
        menu = QMenu(self)
        copyAction = menu.addAction("Copy")
        importAction = menu.addAction("Import File")
        exportAction = menu.addAction("Export Table")
        plotAction = menu.addAction("Plot Selected")
        viewAction = menu.addAction("View Row Data")

        rowsmenu = QMenu("Rows",menu)
        menu.addAction(rowsmenu.menuAction())
        deleteRowsAction = rowsmenu.addAction("Delete Rows")
        addRowsAction = rowsmenu.addAction("Add Rows")
        modemenu = QMenu("Mode",menu)
        menu.addAction(modemenu.menuAction())
        modegroup = QActionGroup(self)
        for i,mode in enumerate(MODES):
            action = QAction(mode, self)
            action = modemenu.addAction(mode)
            action.setCheckable(True)
            action.setData(i)
            action.setActionGroup(modegroup)
            if hasattr(self.parent, 'editMode'):
                action.triggered.connect(self.parent.editMode)
        modegroup.setExclusive(True)

        memAction = menu.addAction("Memory Usage")
        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action == copyAction:
            self.parent.copy()
        elif action == importAction:
            self.parent.importFile()
        elif action == exportAction:
            self.parent.exportTable()
        elif action == plotAction:
            self.parent.plot()
        elif action == viewAction:
            self.viewRow()
        elif action == deleteRowsAction:
            self.deleteRows()
        elif action == addRowsAction:
            self.addRows()
        elif action == memAction:
            self.memory_usage()

    def resetIndex(self):

        self.model.df.reset_index(inplace=True)
        self.refresh()
        return

    def setIndex(self, column):
        """Set column as index"""

        self.storeCurrent()
        self.model.df.set_index(column, inplace=True)
        self.refresh()
        return

    def sortIndex(self, ascending=True):
        """Sort by inde,"""

        self.model.df = self.model.df.sort_index(axis=0,ascending=ascending)
        self.refresh()
        return

    def setIndexType(self):
        """Set the type of the index"""

        types = ['float','int','object','datetime64[ns]']
        newtype, ok = QInputDialog().getItem(self, "New Type",
                                             "Type:", types, 0, False)
        if not ok:
            return
        self.storeCurrent()
        df = self.model.df
        #currtype = df.index.dtype
        df.index = df.index.astype(newtype)
        self.refresh()
        return

    def addColumn(self):
        """Add a  column"""

        opts = {'name':{'label':'Name','type':'entry','default':'' },
                'fill':{'label':'Fill With','type':'entry','default':'' }
                }
        dlg = dialogs.MultipleInputDialog(self, opts, title='Add Column',
                                          width=400,height=150)
        dlg.exec_()
        if not dlg.accepted:
            return False
        name = dlg.values['name']
        fill = dlg.values['fill']

        df = self.model.df
        if not name or name in df.columns:
            return
        if fill != '':
            df[name] = fill
        else:
            df[name] = pd.Series()
        self.refresh()
        return

    def deleteColumn(self, column=None):
        """Delete column"""

        idx = self.getSelectedColumns()
        if len(idx)>0:
            cols = self.model.df.columns[idx]
        else:
            cols = [column]
        reply = QMessageBox.question(self, 'Delete Column(s)?',
                             'Are you sure?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return False

        self.storeCurrent()
        df = self.model.df
        #treat duplicates as unique for deleting
        #dups = df.loc[:,df.columns.duplicated()].columns
        #if len(dups) == 0:
        self.model.df.drop(columns=cols, inplace=True)
        #print (df.columns)
        #else:
        #    keep = [x for x in range(df.shape[1]) if x not in idx]
        #    self.model.df = df.iloc[:, keep]
        self.refresh()
        return

    def addRows(self):
        """Add n rows"""

        num, ok = QInputDialog().getInt(self, "Rows to add",
                                             "Rows:", QLineEdit.Normal)
        if not ok:
            return
        df = self.model.df
        try:
            ind = self.df.index.max()+1
        except:
            ind = len(df)+1
        new = pd.DataFrame(np.nan, index=range(ind,ind+num), columns=df.columns)
        self.model.df = pd.concat([df, new])
        self.refresh()
        return

    def deleteRows(self):
        """Delete rows"""

        rows = self.getSelectedRows()
        reply = QMessageBox.question(self, 'Delete Rows?',
                             'Are you sure?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return False
        idx = self.model.df.index[rows]
        self.model.df = self.model.df.drop(idx)
        self.refresh()
        return

    def viewRow(self):
        """View row data"""

        pd.options.display.max_colwidth = 1000
        df = self.model.df
        rows = self.getSelectedRows()[0]
        idx = df.index[rows]
        row = df.loc[idx]
        text = 'row at index %s' %idx
        dlg = dialogs.TextDialog(self, row.to_string(), title=text, width=800, height=400)
        dlg.exec_()
        return

    def renameColumn(self, column=None):

        name, ok = QInputDialog().getText(self, "Enter New Column Name",
                                             "Name:", QLineEdit.Normal, text=column)
        if ok and name:
            self.model.df.rename(columns={column:name},inplace=True)
            self.refresh()
        return

    def setColumnType(self, column=None):
        """Change the column dtype"""

        idx = self.getSelectedColumns()
        if len(idx)>0:
            cols = self.model.df.columns[idx]
        else:
            cols = [column]
        types = ['float','int','object','datetime64[ns]']
        newtype, ok = QInputDialog().getItem(self, "New Column Type",
                                             "Type:", types, 0, False)
        if not ok:
            return
        self.storeCurrent()
        df = self.model.df
        for c in cols:
            df[c] = df[c].astype(newtype)
        self.refresh()
        return

    def zoomIn(self, fontsize=None):
        """Zoom in table"""

        self.fontsize += 1
        self.updateFont()
        vh = self.verticalHeader()
        h = vh.defaultSectionSize()
        vh.setDefaultSectionSize(h+2)
        self.changeColumnWidths()
        return

    def zoomOut(self, fontsize=None):
        """Zoom out table"""

        self.fontsize -= 1
        self.updateFont()
        vh = self.verticalHeader()
        h = vh.defaultSectionSize()
        vh.setDefaultSectionSize(h-2)
        self.changeColumnWidths(.9)
        return

    def changeColumnWidths(self, factor=1.1):
        """Set column widths"""

        for col in range(len(self.model.df.columns)):
            wi = self.columnWidth(col)
            self.setColumnWidth(col,int(wi*factor))

    def setColumnWidths(self, widths):

        for col in range(len(self.model.df.columns)):
            try:
                self.setColumnWidth(col,widths[col])
            except:
                pass

    def getColumnWidths(self):

        widths=[]
        for col in range(len(self.model.df.columns)):
            widths.append(self.columnWidth(col))
        return widths

class DataFrameModel(QtCore.QAbstractTableModel):
    """
    DataFrame Model class.
    """
    def __init__(self, dataframe=None, *args):
        super(DataFrameModel, self).__init__()
        if dataframe is None:
            self.df = util.getEmptyData()
        else:
            self.df = dataframe
        self.bg = '#F4F4F3'
        self.highlighted = None
        return

    def update(self, df):
        #print('Updating Model')
        self.df = df

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.df.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.df.columns.values)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """Edit or display roles. Handles what happens when the Cells
        are edited or what appears in each cell.
        https://www.pythonguis.com/tutorials/pyside-qtableview-modelviews-numpy-pandas/
        """

        floatfmt = '{0:.%sf}' %PRECISION
        i = index.row()
        j = index.column()
        #print (self.df.dtypes)
        try:
            coltype = self.df.dtypes[j]
        except:
            coltype = self.df[self.df.columns[j]].dtype
        isdate = is_datetime(coltype)
        if role == QtCore.Qt.DisplayRole:
            value = self.df.iloc[i, j]
            if isdate and not value is pd.NaT:
                try:
                    return value.strftime(TIMEFORMAT)
                except:
                    return ''
            elif type(value) != str:
                if type(value) in [float,np.float64] and np.isnan(value):
                    return ''
                elif type(value) in [float,np.float64]:
                    return floatfmt.format(value)
                else:
                    return (str(value))
            else:
                return '{0}'.format(value)
        elif (role == QtCore.Qt.EditRole):
            value = self.df.iloc[i, j]
            #print (coltype)
            #print (value,type(value))
            if type(value) is str:
                return value
            if type(value) in [int,np.int64]:
                return int(value)
            if np.isnan(value):
                return ''
            if type(value) in [float,np.float64]:
                try:
                    return float(value)
                except:
                    return str(value)

        elif role == QtCore.Qt.BackgroundRole:
            if self.highlighted is None:
                return QColor(self.bg)
            value = self.highlighted.iloc[i, j]
            if value == True:
                return QColor('lightblue')
            else:
                return QColor(self.bg)

    def headerData(self, col, orientation, role):
        """What's displayed in the headers"""

        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return str(self.df.columns[col])
            if orientation == QtCore.Qt.Vertical:
                value = self.df.index[col]
                if type( self.df.index) == pd.DatetimeIndex:
                    if not value is pd.NaT:
                        try:
                            return value.strftime(TIMEFORMAT)
                        except:
                            return ''
                else:
                    return str(value)
        return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """Set data upon edits"""

        i = index.row()
        j = index.column()
        curr = self.df.iloc[i,j]
        #print (curr, value)
        self.df.iloc[i,j] = value
        return True

    def flags(self, index):

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable

    def sort(self, idx, ascending=True):
        """Sort table by given column number """

        self.layoutAboutToBeChanged.emit()
        col = self.df.columns[idx]
        self.df = self.df.sort_values(col, ascending=ascending)
        self.layoutChanged.emit()
        return

class SubTableWidget(DataFrameWidget):
    """Widget for sub table"""
    def __init__(self, parent=None, dataframe=None, **args):

        DataFrameWidget.__init__(self, parent, dataframe, **args)
        return

    def createToolbar(self):
        """Override default toolbar"""

        self.setLayout(self.layout)
        items = {'copy': {'action':self.copy,'file':'copy'},
                 'paste': {'action':self.paste,'file':'paste'},
                 'plot': {'action':self.plot,'file':'plot'},
                 'transpose': {'action':self.transpose,'file':'transpose'}
                 }
        toolbar = QToolBar("Toolbar")
        toolbar.setOrientation(QtCore.Qt.Vertical)
        dialogs.addToolBarItems(toolbar, self, items)
        self.layout.addWidget(toolbar,1,2)
        return

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

import sys, os, io
import numpy as np
import pandas as pd
import string
from PySide2 import QtCore, QtGui
from PySide2.QtCore import QObject#, pyqtSignal, pyqtSlot, QPoint
from PySide2.QtWidgets import *
from PySide2.QtGui import *

module_path = os.path.dirname(os.path.abspath(__file__))
iconpath = os.path.join(module_path, 'icons')
font = 'monospace'
fontsize = 12

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
         'interpreter':'interpreter',
         'subtable':'subtable','clear':'clear'
         }

class ColumnHeader(QHeaderView):
    def __init__(self):
        super(QHeaderView, self).__init__()
        return

class DataFrameWidget(QWidget):
    """Widget containing a tableview and toolbars"""
    def __init__(self, parent=None, dataframe=None, app=None,
                 toolbar=True, statusbar=True, *args):

        super(DataFrameWidget, self).__init__()
        self.splitter = QSplitter(Qt.Vertical, self)
        l = self.layout = QGridLayout()
        l.setSpacing(2)
        l.addWidget(self.splitter,1,1)
        self.table = DataFrameTable(self, dataframe, font=font, fontsize=fontsize)
        self.splitter.addWidget(self.table)
        if toolbar == True:
            self.createToolbar()
        if statusbar == True:
            self.statusBar()
        self.pf = None
        self.app = app
        self.pyconsole = None
        self.subtabledock = None
        self.subtable = None
        return

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

        self.toolbar = ToolBar(self)
        self.setLayout(self.layout)
        self.layout.addWidget(self.toolbar,1,2)
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

        if not hasattr(self, 'size_label'):
            return
        df = self.table.model.df
        s = '{r} rows x {c} columns'.format(r=len(df), c=len(df.columns))
        self.size_label.setText(s)
        return

    def load(self):
        return

    def save(self):
        return

    def importFile(self, filename=None, dialog=True, **kwargs):
        """Import csv file"""

        if dialog is True and filename == None:
            options = QFileDialog.Options()
            filename, _ = QFileDialog.getOpenFileName(self,"Import File",
                                 "","CSV files (*.csv);;Text Files (*.txt);;All Files (*)",
                                 options=options)

            dlg = dialogs.ImportDialog(self, filename)
            dlg.exec_()
            if not dlg.accepted:
                return
            self.table.model.df = dlg.df
            self.refresh()
        elif filename != None:
            self.table.model.df = pd.read_csv(filename)
            self.refresh()
        return

    def importExcel(self):
        """Import excel file"""

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

    def importURL(self):
        """Import hdf5 file"""

        url, ok = QInputDialog().getText(self, "Enter URL",
                                             "Name:", QLineEdit.Normal)
        if ok and url:
            self.table.model.df = pd.read_csv(url)
            self.refresh()
        return

    def exportTable(self):
        """Export table"""

        options = QFileDialog.Options()
        options.setDefaultSuffix('csv')
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

        df = self.table.getSelectedDataFrame()
        df.to_clipboard()
        return

    def paste(self):
        """Paste from clipboard"""

        self.table.model.df = pd.read_clipboard(sep='\t')
        self.refresh()
        return

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
        if parent == None:
            self.pf.show()
        return self.pf

    def info(self):
        """Table info"""

        buf = io.StringIO()
        self.table.model.df.info(verbose=True,buf=buf,memory_usage=True)
        td = dialogs.TextDialog(self, buf.getvalue(), 'Info', width=500, height=400)
        return

    def showAsText(self):
        """Show selection as text"""

        df = self.getSelectedDataFrame()
        dlg = dialogs.TextDialog(self, df.to_string(), width=800, height=400)
        dlg.exec_()
        return

    def clear(self):
        """Clear table"""

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
                             'items':['first','last'], 'tooltip':'values to keep'}
                }
        dlg = dialogs.MultipleInputDialog(self, opts, title='Clean Data')
        dlg.exec_()
        if not dlg.accepted:
            return
        kwds = dlg.values
        cols = df.columns
        keep = kwds['keep']
        remove = kwds['remove']
        new = df[df.duplicated(subset=cols,keep=keep)]
        if remove == True:
            self.table.model.df = df.drop_duplicates(subset=cols,keep=keep)
            self.refresh()
        if len(new)>0:
            self.showSubTable(new)
        return

    def cleanData(self):
        """Deal with missing data"""

        df = self.table.model.df
        cols = df.columns
        fillopts = ['fill scalar','','ffill','bfill','interpolate']
        opts = {'method':{'label':'Fill missing method','type':'combobox','default':'',
                             'items':fillopts, 'tooltip':''},
                'symbol':{'label':'Fill empty with','type':'combobox','default':'',
                             'items':['','-','x'], 'tooltip':'seperator'},
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
        if kwds['dropcols'] == 1:
            df = df.dropna(axis=1,how=kwds['how'])
        if kwds['droprows'] == 1:
            df = df.dropna(axis=0,how=kwds['how'])
        if kwds['method'] == '':
            pass
        elif kwds['method'] == 'fill scalar':
            df = df.fillna(kwds['symbol'])
        elif kwds['method'] == 'interpolate':
            df = df.interpolate()
        else:
            df = df.fillna(method=kwds['method'], limit=kwds['limit'])
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

        types = ['float','int']
        opts = {'convert to':  {'type':'combobox','default':'int','items':types,'label':'Convert To',
                                        'tooltip':' '},
                'removetext':  {'type':'checkbox','default':0,'label':'try to remove text',
                                                        'tooltip':' '},
                'convert currency':  {'type':'checkbox','default':0,'label':'convert currency',
                                                        'tooltip':' '},
                'selected columns only':  {'type':'checkbox','default':0,'label':'selected columns only',
                                                        'tooltip':' '},
                'fill empty':  {'type':'checkbox','default':0,'label':'Fill Empty',
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
        fillempty = kwds['fill empty']

        #cols = self.table.multiplecollist
        df = self.table.model.df
        if useselected == 1:
            colnames = df.columns[cols]
        else:
            colnames = df.columns

        for c in colnames:
            x=df[c]
            if fillempty == 1:
                x = x.fillna(0)
            if currency == 1:
                x = x.replace( '[\$\£\€,)]','', regex=True ).replace( '[(]','-', regex=True )
            if removetext == 1:
                x = x.replace( '[^\d.]+', '', regex=True)
            self.table.model.df[c] = pd.to_numeric(x, errors='coerce').astype(convtype)

        self.refresh()
        #self.tableChanged()
        return

    def convertTypes(self):

        dlg = dialogs.ConvertTypesDialog(self, self.table.model.df)
        dlg.exec_()
        if not dlg.accepted:
            return
        return

    def convertColumnNames(self):

        return

    def applyColumnFunction(self, column):
        """Apply column wise functions, applies a calculation per row and
        ceates a new column."""

        df = self.table.model.df
        col = column
        cols=[column]
        #cols = list(df.columns[self.multiplecollist])
        funcs = ['mean','std','max','min','log','exp','log10','log2',
                 'round','floor','ceil','trunc',
                 'sum','subtract','divide','mod','remainder','convolve',
                 'negative','sign','power',
                 'sin','cos','tan','degrees','radians']

        types = ['float','int']
        opts = {'funcname':  {'type':'combobox','default':'int','items':funcs,'label':'Function'},
                'newcol':  {'type':'entry','default':'','items':funcs,'label':'New column name'},
                'inplace':  {'type':'checkbox','default':False,'label':'Update in place'},
                'suffix':  {'type':'entry','default':'_x','items':funcs,'label':'Suffix'},
               }
        dlg = dialogs.MultipleInputDialog(self, opts, title='Apply Function', width=300)
        dlg.exec_()
        if not dlg.accepted:
            return
        kwds = dlg.values

        funcname = kwds['funcname']
        newcol = kwds['newcol']
        inplace = kwds['inplace']
        suffix = kwds['suffix']

        func = getattr(np, funcname)
        if newcol == '':
            if len(cols)>3:
                s = ' %s cols' %len(cols)
            else:
                s =  '(%s)' %(','.join(cols))[:20]
            newcol = funcname + s

        if funcname in ['subtract','divide','mod','remainder','convolve']:
            newcol = cols[0]+' '+ funcname +' '+cols[1]
            df[newcol] = df[cols[0]].combine(df[cols[1]], func=func)
        else:
            if inplace == True:
                newcol = col#s[0]
            df[newcol] = df[col].apply(func, 1)
        #self.table.model.df[column] = data

        #if inplace == False:
        #    self.placeColumn(newcol,cols[-1])
        #else:
        self.refresh()
        return

    def fillData(self, column):
        """Fill column with data"""

        dists = ['normal','gamma','uniform','random int','logistic']
        df = self.table.model.df
        opts = {'random':  {'type':'checkbox','default':0,'label':'Random Noise',
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
        if random == True:
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

        self.table.model.df[column] = data
        self.refresh()
        return

    def convertDates(self, column):
        """Convert single or multiple columns into datetime"""

        df = self.table.model.df
        #cols = list(df.columns[self.multiplecollist])
        '''if len(cols) == 1:
            colname = cols[0]
            temp = df[colname]
        else:
            colname = '-'.join(cols)
            temp = df[cols]'''

        timeformats = ['infer','%d/%m/%Y','%Y/%m/%d','%Y/%d/%m',
                        '%Y-%m-%d %H:%M:%S','%Y-%m-%d %H:%M',
                        '%d-%m-%Y %H:%M:%S','%d-%m-%Y %H:%M']
        props = ['','day','month','hour','minute','second','year',
                 'dayofyear','weekofyear','quarter']
        opts = {'format':  {'type':'combobox','default':'int',
                            'items':timeformats,'label':'Conversion format'},
                'prop':  {'type':'combobox','default':'int',
                        'items':props,'label':'Extract from datetime'} }

        dlg = dialogs.MultipleInputDialog(self, opts, title='Convert Dates')
        dlg.exec_()
        if not dlg.accepted:
            return
        kwds = dlg.values

        format = kwds['format']
        prop = kwds['prop']
        if format == 'infer':
            format = None

        temp = df[column]
        if temp.dtype != 'datetime64[ns]':
            temp = pd.to_datetime(temp, format=format)

        if prop != '':
            new = getattr(temp.dt, prop)
            try:
                new = new.astype(int)
            except:
                pass
            self.table.model.df[prop] = new
        else:
            self.table.model.df[column] = temp
        self.refresh()
        return

    def applyStringMethod(self):
        """Apply string operation to column(s)"""

        df = self.model.df
        cols = list(df.columns[self.multiplecollist])
        col = cols[0]
        funcs = ['','split','strip','lstrip','lower','upper','title','swapcase','len',
                 'slice','replace','concat']
        d = MultipleValDialog(title='Apply Function',
                                initialvalues=(funcs,',',0,1,'','',1),
                                labels=('Function:',
                                        'Split sep:',
                                        'Slice start:',
                                        'Slice end:',
                                        'Pattern:',
                                        'Replace with:',
                                        'In place:'),
                                types=('combobox','string','int',
                                       'int','string','string','checkbutton'),
                                tooltips=(None,'separator for split or concat',
                                          'start index for slice',
                                          'end index for slice',
                                          'characters or regular expression for replace',
                                          'characters to replace with',
                                          'replace column'),
                                parent = self.parentframe)
        if d.result == None:
            return
        self.storeCurrent()
        func = d.results[0]
        sep = d.results[1]
        start = d.results[2]
        end = d.results[3]
        pat = d.results[4]
        repl = d.results[5]
        inplace = d.results[6]
        if func == 'split':
            new = df[col].str.split(sep).apply(pd.Series)
            new.columns = [col+'_'+str(i) for i in new.columns]
            self.model.df = pd.concat([df,new],1)
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
        df[newcol] = x
        if inplace == 0:
            self.placeColumn(newcol,col)
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
            self.splitter.addWidget(dock)

        self.subtabledock.show()
        newtable = SubTableWidget(self.subtabledock, dataframe=df, statusbar=False)
        self.subtabledock.setWidget(newtable)
        self.subtable = newtable
        newtable.show()

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
            self.splitter.addWidget(dock)
            self.pyconsole = interpreter.TerminalPython(dock, table=self.table, app=self.app)
            dock.setWidget(self.pyconsole)
        else:
            self.consoledock.show()
        return

class DataFrameTable(QTableView):
    """
    QTableView with pandas DataFrame as model.
    """
    def __init__(self, parent=None, dataframe=None, font='Arial',
                    fontsize=12, *args):

        QTableView.__init__(self)
        self.parent = parent
        self.clicked.connect(self.showSelection)
        #self.doubleClicked.connect(self.handleDoubleClick)
        #self.setSelectionBehavior(QTableView.SelectRows)
        #self.setSelectionBehavior(QTableView.SelectColumns)

        vh = self.verticalHeader()
        vh.setVisible(True)
        vh.setDefaultSectionSize(28)
        vh.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        vh.customContextMenuRequested.connect(self.rowHeaderMenu)
        #vh.sectionClicked.connect(self.rowClicked)

        hh = self.horizontalHeader()
        hh.setVisible(True)
        #hh.setStretchLastSection(True)
        #hh.setSectionResizeMode(QHeaderView.Interactive)
        hh.setSectionsMovable(True)
        hh.setSelectionMode(QAbstractItemView.ExtendedSelection)
        hh.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        hh.customContextMenuRequested.connect(self.columnHeaderMenu)
        hh.sectionClicked.connect(self.columnSelected)

        #formats
        self.setDragEnabled(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.setCornerButtonEnabled(True)
        self.setSortingEnabled(True)
        self.font = QFont(font)
        self.font.setPointSize(int(fontsize))
        self.setFont(self.font)

        tm = DataFrameModel(dataframe)
        self.setModel(tm)
        self.model = tm
        #self.resizeColumnsToContents()
        self.setWordWrap(False)
        return

    def refresh(self):
        """Refresh table if dataframe is changed"""

        self.font = QFont(font, int(fontsize))
        self.setFont(self.font)
        self.model.beginResetModel()
        self.model.dataChanged.emit(0,0)
        self.model.endResetModel()
        if hasattr(self.parent,'statusbar'):
            self.parent.updateStatusBar()
        return

    def memory_usage(self):

        m = self.model.df.memory_usage(deep=True).sum()
        msg = QMessageBox()
        msg.setText("Memory used: %s bytes" %m)
        msg.setWindowTitle('Memory Usage')
        msg.exec_()
        return

    def showSelection(self, item):

        cellContent = item.data()
        #print(cellContent)  # test
        row = item.row()
        model = item.model()
        columnsTotal= model.columnCount(None)
        return

    def getSelectedRows(self):

        rows=[]
        for idx in self.selectionModel().selectedRows():
            rows.append(idx.row())
        return rows

    def getSelectedColumns(self):

        return self.selectionModel().selectedColumns()

    def getSelectedDataFrame(self):
        """Get selection as a dataframe"""

        df = self.model.df
        rows = list(set([(i.row()) for i in self.selectionModel().selectedIndexes()]))
        cols = list(set([(i.column()) for i in self.selectionModel().selectedIndexes()]))
        return df.iloc[rows,cols]

    def handleDoubleClick(self, item):

        cellContent = item.data()
        return

    def columnClicked(self, col):

        hheader = self.horizontalHeader()
        df = self.model.df
        self.model.df = df.sort_values(df.columns[col])
        return

    def columnSelected(self, col):
        hheader = self.horizontalHeader()

    def sort(self, col):

        df = self.model.df
        self.model.df = df.sort_values(col)
        return

    def storeCurrent(self):
        """Store current version of the table before a major change is made"""

        self.prevdf = self.model.df.copy()
        return

    def deleteCells(self, rows, cols, answer=None):
        """Clear the cell contents"""

        if answer == None:
            answer = QMessageBox.question(self, 'Delete Cells?',
                             'Are you sure?', QMessageBox.Yes, QMessageBox.No)
        if not answer:
            return
        self.storeCurrent()
        print (rows, cols)
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
        action = menu.exec_(self.mapToGlobal(pos))
        if action == resetIndexAction:
            self.resetIndex()
        return

    def columnHeaderMenu(self, pos):
        """Column header right click popup menu"""

        hheader = self.horizontalHeader()
        idx = hheader.logicalIndexAt(pos)
        column = self.model.df.columns[idx]
        #model = self.model
        menu = QMenu(self)

        sortAction = menu.addAction("Sort ")
        iconw = QIcon.fromTheme("open")
        sortAction.setIcon(iconw)
        setIndexAction = menu.addAction("Set as Index")

        colmenu = QMenu("Column",menu)
        deleteColumnAction = colmenu.addAction("Delete Column")
        renameColumnAction = colmenu.addAction("Rename Column")
        addColumnAction = colmenu.addAction("Add Column")
        menu.addAction(colmenu.menuAction())
        fillAction = menu.addAction("Fill Data")
        applyFunctionAction = menu.addAction("Apply Function")
        datetimeAction = menu.addAction("Date/Time Conversion")

        #sortAction = menu.addAction("Sort By")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == sortAction:
            self.sort(column)
        elif action == deleteColumnAction:
            self.deleteColumn(column)
        elif action == renameColumnAction:
            self.renameColumn(column)
        elif action == addColumnAction:
            self.addColumn()
        elif action == setIndexAction:
            self.setIndex(column)
        elif action == datetimeAction:
            self.parent.convertDates(column)
        elif action == fillAction:
            self.parent.fillData(column)
        elif action == applyFunctionAction:
            self.parent.applyColumnFunction(column)
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
        rowsmenu = QMenu("Rows",menu)
        menu.addAction(rowsmenu.menuAction())
        deleteRowsAction = rowsmenu.addAction("Delete Rows")
        addRowsAction = rowsmenu.addAction("Add Rows")

        memAction = menu.addAction("Memory Usage")
        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action == copyAction:
            self.parent.copy()
        elif action == importAction:
            self.importFile()
        elif action == exportAction:
            self.parent.exportTable()
        elif action == plotAction:
            self.parent.plot()
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

        self.model.df.set_index(column, inplace=True)
        self.refresh()
        return

    def addColumn(self):
        """Add a  column"""

        df = self.model.df
        name, ok = QInputDialog().getText(self, "Enter Column Name",
                                             "Name:", QLineEdit.Normal)
        if ok and name:
            if name in df.columns:
                return
            df[name] = pd.Series()
            self.refresh()
        return

    def deleteColumn(self, column=None):

        reply = QMessageBox.question(self, 'Delete Rows?',
                             'Are you sure?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return False
        self.model.df = self.model.df.drop(columns=[column])
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
        print (self.selectionModel().selectedRows())

        idx = self.model.df.index[rows]
        self.model.df = self.model.df.drop(idx)
        self.refresh()
        return

    def renameColumn(self, column=None):

        name, ok = QInputDialog().getText(self, "Enter New Column Name",
                                             "Name:", QLineEdit.Normal)
        if ok and name:
            self.model.df.rename(columns={column:name},inplace=True)
            self.refresh()
        return

    def zoomIn(self, fontsize=None):

        if fontsize == None:
            s = self.font.pointSize()+1
        else:
            s = fontsize
        self.font.setPointSize(s)
        self.setFont(self.font)
        vh = self.verticalHeader()
        h = vh.defaultSectionSize()
        vh.setDefaultSectionSize(h+2)
        return

    def zoomOut(self, fontsize=None):

        if fontsize == None:
            s = self.font.pointSize()-1
        else:
            s = fontsize
        self.font.setPointSize(s)
        self.setFont(self.font)
        vh = self.verticalHeader()
        h = vh.defaultSectionSize()
        vh.setDefaultSectionSize(h-2)
        return

    def changeColumnWidths(self, factor=1.1):

        for col in range(len(self.model.df.columns)):
            w=self.columnWidth(col)
            self.setColumnWidth(col,w*factor)


class DataFrameModel(QtCore.QAbstractTableModel):
    def __init__(self, dataframe=None, *args):
        super(DataFrameModel, self).__init__()
        if dataframe is None:
            self.df = util.getEmptyData()
        else:
            self.df = dataframe
        self.bg = '#F4F4F3'
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
        """

        i = index.row()
        j = index.column()
        if role == QtCore.Qt.DisplayRole:
            value = self.df.iloc[i, j]
            if type(value) != str:
                if type(value) == float and np.isnan(value):
                    return ''
                else:
                    return (str(value))
            else:
                return '{0}'.format(value)
        elif (role == QtCore.Qt.EditRole):
            value = self.df.iloc[i, j]
            print (value, type(value))
            if np.isnan(value):
                return ''
            else:
                return value
        elif role == QtCore.Qt.BackgroundRole:
            return QColor(self.bg)

    def headerData(self, col, orientation, role):
        """What's displayed in the headers"""

        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.df.columns[col]
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return self.df.index[col]
        return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """Set data upon edits"""

        i = index.row()
        j = index.column()
        curr = self.df.iloc[i,j]
        print (curr, value)
        self.df.iloc[i,j] = value
        return True

    def flags(self, index):

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable

    def sort(self, idx, order):
        """Sort table by given column number """

        self.layoutAboutToBeChanged.emit()
        col = self.df.columns[idx]
        self.df = self.df.sort_values(col)
        self.layoutChanged.emit()
        return

class SubTableWidget(DataFrameWidget):
    """Widget for sub table"""
    def __init__(self, parent=None, dataframe=None, **args):

        DataFrameWidget.__init__(self, parent, dataframe, **args)
        return

    def createToolbar(self):
        """Override default toolbar"""

        self.toolbar = SubToolBar(self)
        self.setLayout(self.layout)
        self.layout.addWidget(self.toolbar, 1, 2)
        return

class ToolBar(QWidget):
    """Toolbar class for side buttons"""
    def __init__(self, app, parent=None):
        super(ToolBar, self).__init__(parent)
        self.parent = parent
        self.app = app
        self.layout = QVBoxLayout()
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.setContentsMargins(2,2,2,2)
        self.setLayout(self.layout)
        self.createButtons()
        self.setMaximumWidth(40)
        return

    def createButtons(self):
        """Toolbar buttons"""

        funcs = {'load':self.app.load,
                 'importexcel': self.app.importExcel,
                 'save':self.app.save,
                 'copy':self.app.copy, 'paste':self.app.paste,
                 'plot':self.app.plot,
                 'transpose':self.app.transpose,
                 'aggregate':self.app.aggregate,
                 'pivot':self.app.pivot,
                 'melt':self.app.melt,
                 'merge':self.app.merge,
                 'subtable':self.app.subTableFromSelection,
                 'interpreter':self.app.showInterpreter,
                 'clear':self.app.clear}

        tooltips = {'load':'load table', 'save':'export',
                    'importexcel':'import excel file',
                    'copy':'copy','paste':'paste',
                    'transpose':'transpose table', 'aggregate':'groupby-aggregate',
                    'pivot':'pivot table','melt':'melt table',
                    'merge':'merge two tables',
                    'subtable':'sub-table from selection',
                    'interpreter':'show python interpreter',
                    'clear':'clear table'}
        for name in funcs:
            tip=None
            shortcut=None
            if name in tooltips:
                tip=tooltips[name]
            self.addButton(name, funcs[name], icons[name], tip)

    def addButton(self, name, function, icon, tooltip=None):
        """Add named button"""

        layout=self.layout
        button = QPushButton(name)
        button.setGeometry(QtCore.QRect(26,26,26,26))
        button.setText('')
        iconfile = os.path.join(iconpath,icon+'.png')
        if os.path.exists(iconfile):
            button.setIcon(QIcon(iconfile))
        else:
            iconw = QIcon.fromTheme(icon)
            button.setIcon(QIcon(iconw))
        button.setIconSize(QtCore.QSize(24,24))
        if tooltip is not None:
            button.setToolTip(tooltip)
        button.clicked.connect(function)
        button.setMinimumWidth(26)
        layout.addWidget(button)
        return

class SubToolBar(ToolBar):
    def __init__(self, app, parent=None):
        ToolBar.__init__(self, app, parent)
        return

    def createButtons(self):
        funcs = {'copy': self.app.copy,
                 'paste':self.app.paste,
                 'transpose':self.app.transpose,
                 'plot':self.app.plot}
        tooltips = {'plot':'plot','copy':'copy selection','paste':'paste selection'}
        for name in funcs:
            tip=None
            if name in tooltips:
                tip=tooltips[name]
            self.addButton(name, funcs[name], icons[name], tip)
        return

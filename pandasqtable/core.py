# -*- coding: utf-8 -*-

"""
    Implements a core classes for pandasqtable
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

from PySide2 import QtCore, QtGui
from PySide2.QtCore import QObject#, pyqtSignal, pyqtSlot, QPoint
from PySide2.QtWidgets import *
from PySide2.QtGui import *
import sys, os, io
import numpy as np
import pandas as pd
import string

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
from . import config, dialogs, plotting, util


class ColumnHeader(QHeaderView):
    def __init__(self):
        super(QHeaderView, self).__init__()
        return

class DataFrameWidget(QWidget):
    """Widget containing a tableview and toolbars"""
    def __init__(self, parent=None, dataframe=None, *args):

        super(DataFrameWidget, self).__init__()
        l = self.layout = QGridLayout()
        l.setSpacing(2)
        self.table = DataFrameTable(self, dataframe)
        l.addWidget(self.table, 1, 1)
        self.createToolbar()
        self.pf = None
        return

    def createToolbar(self):
        self.toolbar = ToolBar(self)
        self.setLayout(self.layout)
        self.layout.addWidget(self.toolbar, 1, 2)

    def load(self, filename=None):
        return

    def save(self):
        return

    def importFile(self, filename=None, dialog=False, **kwargs):

        if dialog is True:
            options = QFileDialog.Options()
            filename, _ = QFileDialog.getOpenFileName(self,"Import File",
                                                      "","All Files (*);;Text Files (*.txt);;CSV files (*.csv)",
                                                      options=options)


            df = pd.read_csv(filename, **kwargs)
            self.table.model.df = df
        return

    def copy(self):
        return

    def paste(self):
        return

    def plot(self):
        self.table.pf.replot()
        return

    def redraw(self):
        return

    def createPlotViewer(self, parent):
        """Create a plot widget attached to this table"""

        if self.pf == None:
            self.pf = plotting.PlotViewer(table=self.table, parent=parent)
        return self.pf

    def pivot(self):
        """Pivot table"""

        return

    def info(self):

        buf = io.StringIO()
        self.table.model.df.info(verbose=True,buf=buf,memory_usage=True)
        td = dialogs.TextDialog(self, buf.getvalue(), 'Info')
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
        #self.redraw()
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

        convtype = d.results[0]
        currency = d.results[1]
        removetext = d.results[2]
        useselected = d.results[3]
        fillempty = d.results[4]

        cols = self.multiplecollist
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
            self.model.df[c] = pd.to_numeric(x, errors='coerce').astype(convtype)

        self.redraw()
        self.tableChanged()
        return

    def showasText(self):

        return

    def convertColumnNames(self):

        return

    def createChildTable(self, df, title=None, index=False, out=False):
        """Add the child table"""

        self.closeChildTable()
        if out == True:
            win = QWindow()
        else:
            win = QWidget(self.parentframe)

        self.childframe = win
        newtable = self.__class__(win, dataframe=df, showtoolbar=0, showstatusbar=1)
        newtable.parenttable = self
        newtable.adjustColumnWidths()
        newtable.show()
        toolbar = ChildToolBar(win, newtable)
        toolbar.grid(row=0,column=3,rowspan=2,sticky='news')
        self.child = newtable
        if hasattr(self, 'pf'):
            newtable.pf = self.pf
        if index==True:
            newtable.showIndex()
        return

class DataFrameTable(QTableView):
    """
    QTableView with pandas DataFrame as model.
    """
    def __init__(self, parent=None, dataframe=None, fontsize=12, *args):
        QTableView.__init__(self)
        self.clicked.connect(self.showSelection)
        #self.doubleClicked.connect(self.handleDoubleClick)
        self.setSelectionBehavior(QTableView.SelectRows)
        #self.setSelectionBehavior(QTableView.SelectColumns)
        #self.horizontalHeader = ColumnHeader()
        header = self.horizontalHeader()
        #header.setResizeMode(QHeaderView.ResizeToContents)
        vh = self.verticalHeader()
        vh.setVisible(True)
        vh.setDefaultSectionSize(28)
        hh = self.horizontalHeader()
        hh.setVisible(True)
        #hh.setStretchLastSection(True)
        #hh.setSectionResizeMode(QHeaderView.Interactive)
        hh.setSectionsMovable(True)
        hh.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        hh.customContextMenuRequested.connect(self.columnHeaderMenu)
        hh.sectionClicked.connect(self.columnClicked)
        self.setDragEnabled(True)
        #self.setSortingEnabled(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.resizeColumnsToContents()
        self.setCornerButtonEnabled(True)
        self.setSortingEnabled(True)

        self.font = QFont("Arial", fontsize)
        #print (fontsize)
        self.setFont(self.font)
        tm = DataFrameModel(dataframe)
        self.setModel(tm)
        self.model = tm
        #self.resizeColumnsToContents()
        self.setWordWrap(False)
        return

    def refresh(self):

        self.model.beginResetModel()
        self.model.dataChanged.emit(0,0)
        self.model.endResetModel()
        return
        
    def showSelection(self, item):

        cellContent = item.data()
        print(cellContent)  # test
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
        #indexes = self.selectionModel().selectedIndexes()
        return self.selectionModel().selectedColumns()

    def getSelectedDataFrame(self):

        df = self.model.df
        #print (self.selectionModel().selectedRows())
        rows=[]
        for idx in self.selectionModel().selectedRows():
            rows.append(idx.row())
        cols=[]
        #print (self.selectionModel().selectedColumns())
        return df.iloc[rows]

    def handleDoubleClick(self, item):

        cellContent = item.data()
        print (item)
        return

    def columnClicked(self, col):

        hheader = self.horizontalHeader()
        df = self.model.df
        self.model.df = df.sort_values(df.columns[col])
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

    def editCell(self, item):
        return

    def setRowColor(self, rowIndex, color):
        for j in range(self.columnCount()):
            self.item(rowIndex, j).setBackground(color)

    def columnHeaderMenu(self, pos):

        hheader = self.horizontalHeader()
        idx = hheader.logicalIndexAt(pos)
        column = self.model.df.columns[idx]
        #model = self.model
        menu = QMenu(self)
        #setIndexAction = menu.addAction("Set as Index")
        deleteColumnAction = menu.addAction("Delete Column")
        renameColumnAction = menu.addAction("Rename Column")
        addColumnAction = menu.addAction("Add Column")
        exportAction = menu.addAction("Export Table")
        #sortAction = menu.addAction("Sort By")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == deleteColumnAction:
            self.deleteColumn(column)
        elif action == renameColumnAction:
            self.renameColumn(column)
        elif action == addColumnAction:
            self.addColumn()
        elif action == exportAction:
            self.exportTable()
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
        model = self.model
        row = model.df.loc[row]
        # Show a context menu for empty space at bottom of table...
        menu = QMenu(self)
        copyAction = menu.addAction("Copy")
        colorAction = menu.addAction("Set Color")
        importAction = menu.addAction("Import")
        prefsAction = menu.addAction("Preferences")
        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action == copyAction:
            self.copy()
        elif action == importAction:
            self.importFile()
        elif action == colorAction:
            pass
        elif action == prefsAction:
            config.PreferencesDialog(self)

    def setIndex(self):

        return

    def copy(self):
        self.model.df
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

    def deleteRows(self):

        rows = self.getSelectedRows()
        reply = QMessageBox.question(self, 'Delete Rows?',
                             'Are you sure?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return False
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

    def importFile(self):
        dialogs.ImportDialog(self)
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
        """Edir or display roles """

        i = index.row()
        j = index.column()
        if role == QtCore.Qt.DisplayRole:
            value = self.df.iloc[i, j]
            if type(value) != str and np.isnan(value):
                return ''
            else:
                return '{0}'.format(value)
        elif (role == QtCore.Qt.EditRole):
            value = self.df.iloc[i, j]
            if value == '':
                return np.nan
            else:
                return value
        elif role == QtCore.Qt.BackgroundRole:
            return QColor(self.bg)

    def headerData(self, col, orientation, role):
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
        #print (curr, value)
        self.df.iloc[i,j] = value
        return True

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable

    def sort(self, Ncol, order):
        """Sort table by given column number """

        self.layoutAboutToBeChanged.emit()
        col = self.df.columns[Ncol]
        self.df = self.df.sort_values(col)
        self.layoutChanged.emit()
        return

class ToolBar(QWidget):
    """Toolbar class"""
    def __init__(self, table, parent=None):
        super(ToolBar, self).__init__(parent)
        self.parent = parent
        self.table = table
        self.layout = QVBoxLayout()
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.setContentsMargins(2,2,2,2)
        self.setLayout(self.layout)
        self.createButtons()
        self.setMaximumWidth(40)
        return

    def createButtons(self):

        funcs = {'load':self.table.load, 'save':self.table.save,
                 'importexcel': self.table.load,
                 'copy':self.table.copy, 'paste':self.table.paste,
                 'plot':self.table.plot,
                 'transpose':self.table.pivot,
                 'pivot':self.table.pivot}
        icons = {'load': 'document-new', 'save': 'document-save-as',
                 'importexcel': 'x-office-spreadsheet',
                 'copy': 'edit-copy', 'paste': 'edit-paste',
                 'plot':'insert-image',
                 'transpose':'object-rotate-right',
                 'pivot': 'edit-undo',
                 }
        for name in funcs:
            self.addButton(name, funcs[name], icons[name])

    def addButton(self, name, function, icon):

        layout=self.layout
        button = QPushButton(name)
        button.setGeometry(QtCore.QRect(30,40,30,40))
        button.setText('')
        iconw = QIcon.fromTheme(icon)
        button.setIcon(QIcon(iconw))
        button.setIconSize(QtCore.QSize(20,20))
        button.clicked.connect(function)
        button.setMinimumWidth(30)
        layout.addWidget(button)

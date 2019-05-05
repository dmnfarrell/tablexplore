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

    def copy(self):
        return

    def paste(self):
        return

    def plot(self):
        self.table.pf.replot()
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

class DataFrameTable(QTableView):
    """
    QTableView with pandas DataFrame as model.
    """
    def __init__(self, parent=None, dataframe=None, *args):
        super(DataFrameTable, self).__init__()
        self.clicked.connect(self.showSelection)
        self.doubleClicked.connect(self.handleDoubleClick)
        self.setSelectionBehavior(QTableView.SelectRows)
        #self.setSelectionBehavior(QTableView.SelectColumns)
        #self.horizontalHeader = ColumnHeader()
        vh = self.verticalHeader()
        vh.setVisible(True)
        hh = self.horizontalHeader()
        hh.setStretchLastSection(True)
        hh.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        hh.customContextMenuRequested.connect(self.columnHeaderMenu)

        self.setDragEnabled(True)
        #self.setSortingEnabled(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.resizeColumnsToContents()

        font = QFont("Arial", 12)
        self.setFont(font)
        tm = TableModel(dataframe)
        self.setModel(tm)
        self.model = tm
        return

    def showSelection(self, item):

        cellContent = item.data()
        print(cellContent)  # test
        row = item.row()
        model = item.model()
        columnsTotal= model.columnCount(None)

        return

    def getSelectedDataFrame(self):

        df = self.model.df
        #print (self.selectionModel().selectedRows())
        rows=[]
        for idx in self.selectionModel().selectedRows():
            rows.append(idx.row())
        cols=[]
        print (self.selectionModel().selectedColumns())
        return df.iloc[rows]

    def handleDoubleClick(self, item):

        cellContent = item.data()
        print (item)
        return

    def editCell(self, item):
        return

    def setRowColor(self, rowIndex, color):
        for j in range(self.columnCount()):
            self.item(rowIndex, j).setBackground(color)

    def columnHeaderMenu(self, pos):

        hheader = self.horizontalHeader()
        column = hheader.logicalIndexAt(hheader.mapFromGlobal(pos))
        print (column)
        model = self.model
        menu = QMenu(self)
        setIndexAction = menu.addAction("Set as Index")
        sortAction = menu.addAction("Sort By")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == setIndexAction:
            self.setIndex()
        return

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

    def importFile(self):
        dialogs.ImportDialog(self)
        return

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, dataframe=None, *args):
        super(TableModel, self).__init__()
        if dataframe is None:
            self.df = util.getEmptyData()
        else:
            self.df = dataframe
        self.bg = '#F4F4F3'
        return

    def update(self, df):
        print('Updating Model')
        self.df = df

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.df.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.df.columns.values)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            i = index.row()
            j = index.column()
            value = self.df.ix[i, j]
            if type(value) is float and np.isnan(value):
                return ''
            else:
                return '{0}'.format(value)

        elif role == QtCore.Qt.BackgroundRole:
            return QColor(self.bg)

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.df.columns[col]
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return self.df.index[col]
        return None

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
                 'pivot':self.table.pivot}
        icons = {'load': 'document-open', 'save': 'document-save-as',
                 'importexcel': 'x-office-spreadsheet',
                 'copy': 'edit-copy', 'paste': 'edit-paste',
                 'plot':'plot',
                 'pivot': 'edit-undo' }
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

# -*- coding: utf-8 -*-

"""
    core module
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

#from pandasqt.compat import QtCore, QtGui, Qt, Slot, Signal
from PySide2 import QtCore, QtGui
from PySide2.QtCore import QObject#, pyqtSignal, pyqtSlot, QPoint
from PySide2.QtWidgets import *
from PySide2.QtGui import *
#from models import DataFrameModel

import numpy as np
import pandas as pd
import string

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


def get_sample_data(rows=400, cols=5):
    """Generate sample data"""

    colnames = list(string.ascii_lowercase[:cols])
    coldata = [np.random.normal(x,1,rows) for x in np.random.normal(5,3,cols)]
    n = np.array(coldata).T
    df = pd.DataFrame(n, columns=colnames)
    df['b'] = df.a*np.random.normal(.8, 0.1, len(df))
    df = np.round(df, 3)
    cats = ['green','blue','red','orange','yellow']
    df['label'] = [cats[i] for i in np.random.randint(0,5,rows)]
    df['date'] = pd.date_range('1/1/2014', periods=rows, freq='H')
    return df

class DataFrameTable(QTableView):
    def __init__(self, parent=None, model=None, *args):
        super(DataFrameTable, self).__init__()
        self.clicked.connect(self.showSelection)
        self.setSelectionBehavior(QTableView.SelectRows)
        #headerView = QHeaderView(self)
        #self.setHorizontalHeader(headerView)
        self.setDragEnabled(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        tm = TableModel()
        self.setModel(tm)
        self.model = tm
        return

    def showSelection(self, item):
        print (item)
        cellContent = item.data()
        print(cellContent)  # test
        row = item.row()
        model = item.model()
        columnsTotal= model.columnCount(None)

        return

    def editCell(self, item):
        return

    def setRowColor(self, rowIndex, color):
        for j in range(self.columnCount()):
            self.item(rowIndex, j).setBackground(color)

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


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None, *args):
        super(TableModel, self).__init__()
        self.df = get_sample_data(50,2)
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
            return '{0}'.format(self.df.ix[i, j])

        elif role == QtCore.Qt.BackgroundRole:
            return QColor(self.bg)

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.df.columns[col]
        return None

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled

    def sort(self, Ncol, order):
        """Sort table by given column number """

        self.layoutAboutToBeChanged.emit()
        col = self.df.columns[Ncol]
        self.df = self.df.sort_values(col)
        self.layoutChanged.emit()
        return

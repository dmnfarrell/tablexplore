#!/usr/bin/env python
"""
    Implements some dialog utilities for tableexplore
    Created Feb 2019
    Copyright (C) Damien Farrell

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 3
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
import math, time
import os, types, io
import string, copy
from collections import OrderedDict
import pandas as pd
try:
    import configparser
except:
    import ConfigParser as configparser
from PySide2 import QtCore, QtGui
from PySide2.QtCore import QObject
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from . import util

def dialogFromOptions(parent, opts, sections=None,
                      wrap=2, section_wrap=4,
                      style=None):
    """
    Get Qt widgets dialog from a dictionary of options.
    Args:
        opts: options dictionary
        sections:
        section_wrap: how many sections in one row
        style: stylesheet css if required
    """

    sizepolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    sizepolicy.setHorizontalStretch(0)
    sizepolicy.setVerticalStretch(0)

    if style == None:
        style = '''
        QLabel {
            font-size: 10px;
        }
        QWidget {
            max-width: 250px;
            min-width: 60px;
            font-size: 14px;
        }
        QPlainTextEdit {
            max-height: 80px;
        }
        '''

    if sections == None:
        sections = {'options': opts.keys()}

    widgets = {}
    dialog = QWidget(parent)
    dialog.setSizePolicy(sizepolicy)

    l = QGridLayout(dialog)
    l.setSpacing(1)
    l.setAlignment(QtCore.Qt.AlignLeft)
    scol=1
    srow=1
    for s in sections:
        row=srow
        col=1
        f = QWidget()
        f.resize(50,100)
        f.sizeHint()
        l.addWidget(f,row,scol)
        gl = QGridLayout(f)
        gl.setAlignment(QtCore.Qt.AlignTop)
        gl.setSpacing(5)
        for o in sections[s]:
            label = o
            val = None
            opt = opts[o]
            if 'label' in opt:
                label = opt['label']
            val = opt['default']
            t = opt['type']
            lbl = QLabel(label)
            gl.addWidget(lbl,row,col)
            lbl.setStyleSheet(style)
            if t == 'combobox':
                w = QComboBox()
                w.addItems(opt['items'])
                w.setCurrentIndex(0)
            elif t == 'entry':
                w = QLineEdit()
                w.setText(str(val))
            elif t == 'textarea':
                w = QPlainTextEdit()
                #w.setSizePolicy(sizepolicy)
                w.insertPlainText(str(val))
            elif t == 'slider':
                w = QSlider(QtCore.Qt.Horizontal)
                s,e = opt['range']
                w.setTickInterval(opt['interval'])
                w.setSingleStep(opt['interval'])
                w.setMinimum(s)
                w.setMaximum(e)
                w.setTickPosition(QSlider.TicksBelow)
                w.setValue(val)
            elif t == 'spinbox':
                w = QSpinBox()
                w.setValue(val)
            elif t == 'checkbox':
                w = QCheckBox()
                w.setChecked(val)
            elif t == 'font':
                w = QFontComboBox()
                w.resize(w.sizeHint())
                w.setCurrentIndex(1)
            col+=1
            gl.addWidget(w,row,col)
            w.setStyleSheet(style)
            widgets[o] = w
            #print (o, row, col)
            if col>=wrap:
                col=1
                row+=1
            else:
                col+=2

        if scol >= section_wrap:
            scol=1
            srow+=2
        else:
            scol+=1
    return dialog, widgets

def getWidgetValues(widgets):
    """Get values back from a set of widgets"""

    kwds = {}
    for i in widgets:
        val = None
        if i in widgets:
            w = widgets[i]
            if type(w) is QLineEdit:
                val = w.text()
            elif type(w) is QPlainTextEdit:
                val = w.toPlainText()
            elif type(w) is QComboBox or type(w) is QFontComboBox:
                val = w.currentText()
            elif type(w) is QCheckBox:
                val = w.isChecked()
            elif type(w) is QSlider:
                val = w.value()
            elif type(w) is QSpinBox:
                val = w.value()
            if val != None:
                kwds[i] = val
    kwds = kwds
    return kwds

def setWidgetValues(widgets, values):
    """Set values for a set of widgets from a dict"""

    kwds = {}
    for i in values:
        val = values[i]
        if i in widgets:
            #print (i, val, type(val))
            w = widgets[i]
            if type(w) is QLineEdit:
                w.setText(str(val))
            elif type(w) is QPlainTextEdit:
                w.insertPlainText(str(val))
            elif type(w) is QComboBox or type(w) is QFontComboBox:
                w.setCurrentIndex(1)
            elif type(w) is QCheckBox:
                w.setChecked(val)
            elif type(w) is QSlider:
                w.setValue(val)
            elif type(w) is QSpinBox:
                w.setValue(val)
    return

class PlainTextEditor(QPlainTextEdit):
    def __init__(self, parent=None, **kwargs):
        super(PlainTextEditor, self).__init__(parent, **kwargs)
        font = QFont("Monospace")
        font.setPointSize(10)
        font.setStyleHint(QFont.TypeWriter)
        self.setFont(font)
        return

    def zoom(self, delta):
        if delta < 0:
            self.zoomOut(1)
        elif delta > 0:
            self.zoomIn(1)

    def contextMenuEvent(self, event):

        menu = QMenu(self)
        copyAction = menu.addAction("Copy")
        clearAction = menu.addAction("Clear")
        zoominAction = menu.addAction("Zoom In")
        zoomoutAction = menu.addAction("Zoom Out")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == copyAction:
            self.copy()
        elif action == clearAction:
            self.clear()
        elif action == zoominAction:
            self.zoom(1)
        elif action == zoomoutAction:
            self.zoom(-1)

class TextDialog(QDialog):
    """Text edit dialog"""
    def __init__(self, parent, text='', title='Text', width=400, height=300):
        super(TextDialog, self).__init__(parent)
        self.resize(width, height)
        self.setWindowTitle(title)
        vbox = QVBoxLayout(self)
        b = self.textbox = PlainTextEditor(self)
        b.insertPlainText(text)
        b.move(10,10)
        b.resize(400,300)
        vbox.addWidget(self.textbox)
        #self.b.setFontFamily('fixed')
        buttonbox = QDialogButtonBox(self)
        buttonbox.setStandardButtons(QDialogButtonBox.Ok)
        buttonbox.button(QDialogButtonBox.Ok).clicked.connect(self.close)
        vbox.addWidget(buttonbox)
        self.show()
        return

class MultipleInputDialog(QDialog):
    """Qdialog with multiple inputs"""
    def __init__(self, parent, options=None, title='Input'):
        super(MultipleInputDialog, self).__init__(parent)
        self.values = None
        self.accepted = False
        self.setMinimumSize(500, 300)
        self.setWindowTitle(title)
        dialog, self.widgets = dialogFromOptions(self, options)
        vbox = QVBoxLayout(self)
        vbox.addWidget(dialog)
        buttonbox = QDialogButtonBox(self)
        buttonbox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        buttonbox.button(QDialogButtonBox.Ok).clicked.connect(self.accept)
        buttonbox.button(QDialogButtonBox.Cancel).clicked.connect(self.close)
        vbox.addWidget(buttonbox)
        self.show()
        return self.values

    def accept(self):
        self.values = getWidgetValues(self.widgets)
        self.accepted = True
        self.close()
        return

class ImportDialog(QDialog):
    """Provides a dialog for import settings"""

    def __init__(self, parent=None, filename=None):

        from .core import DataFrameTable
        super(ImportDialog, self).__init__(parent)
        self.parent = parent
        self.filename = filename
        self.df = None

        self.parent = parent
        self.setWindowTitle('Import File')
        self.createWidgets()
        self.setGeometry(QtCore.QRect(250, 250, 900, 600))

        self.update()
        self.show()
        return

    def createWidgets(self):
        """Create widgets"""

        delimiters = [',',r'\t',' ',';','/','&','|','^','+','-']
        encodings = ['utf-8','ascii','iso8859_15','cp037','cp1252','big5','euc_jp']
        timeformats = ['infer','%d/%m/%Y','%Y/%m/%d','%Y/%d/%m',
                        '%Y-%m-%d %H:%M:%S','%Y-%m-%d %H:%M',
                        '%d-%m-%Y %H:%M:%S','%d-%m-%Y %H:%M']
        grps = {'formats':['delimiter','decimal','comment'],
                'data':['skiprows','index_col','skipinitialspace',
                        'skip_blank_lines','parse_dates','time format','encoding','names'],
                'other':['rowsperfile']}
        grps = OrderedDict(sorted(grps.items()))
        opts = self.opts = {'delimiter':{'type':'combobox','default':',',
                        'items':delimiters, 'tooltip':'seperator'},
                     #'header':{'type':'entry','default':0,'label':'header',
                     #          'tooltip':'position of column header'},
                     'index_col':{'type':'entry','default':'','label':'index col',
                                'tooltip':''},
                     'decimal':{'type':'combobox','default':'.','items':['.',','],
                                'tooltip':'decimal point symbol'},
                     'comment':{'type':'entry','default':'#','label':'comment',
                                'tooltip':'comment symbol'},
                     'skipinitialspace':{'type':'checkbox','default':0,'label':'skip initial space',
                                'tooltip':'skip initial space'},
                     'skiprows':{'type':'entry','default':0,'label':'skiprows',
                                'tooltip':'rows to skip'},
                     'skip_blank_lines':  {'type':'checkbutton','default':0,'label':'skip blank lines',
                                'tooltip':'do not use blank lines'},
                     'parse_dates':  {'type':'checkbox','default':1,'label':'parse dates',
                                'tooltip':'try to parse date/time columns'},
                     'time format': {'type':'combobox','default':'','items':timeformats,
                                'tooltip':'date/time format'},
                     'encoding':{'type':'combobox','default':'utf-8','items':encodings,
                                'tooltip':'file encoding'},
                     #'prefix':{'type':'entry','default':None,'label':'prefix',
                     #           'tooltip':''}
                     'rowsperfile':{'type':'entry','default':'','label':'rows per file',
                                'tooltip':'rows to read'},
                     'names':{'type':'entry','default':'','label':'column names',
                                'tooltip':'col labels'},
                     }

        optsframe, self.widgets = dialogFromOptions(self, opts, grps, wrap=1, section_wrap=1)
        layout = QGridLayout()
        layout.setColumnStretch(1,2)
        layout.addWidget(optsframe,1,1)
        optsframe.setMaximumWidth(300)
        bf = self.createButtons(optsframe)
        layout.addWidget(bf,2,1)

        main = QSplitter(self)
        main.setOrientation(QtCore.Qt.Vertical)
        layout.addWidget(main,1,2,2,1)

        self.textarea = PlainTextEditor(main)
        main.addWidget(self.textarea)
        self.textarea.resize(200,200)
        from .core import DataFrameTable
        t = self.previewtable = DataFrameTable(main)
        main.addWidget(t)
        self.setLayout(layout)
        return

    def createButtons(self, parent):

        bw = self.button_widget = QWidget(parent)
        vbox = QVBoxLayout(bw)
        button = QPushButton("Update")
        button.clicked.connect(self.update)
        vbox.addWidget(button)
        button = QPushButton("Import")
        button.clicked.connect(self.doImport)
        vbox.addWidget(button)
        button = QPushButton("Cancel")
        button.clicked.connect(self.quit)
        vbox.addWidget(button)
        return bw

    def showText(self):
        """show text contents"""

        with open(self.filename, 'r') as stream:
            try:
                text = stream.read()
            except:
                text = 'failed to preview, check encoding and then update preview'
        self.textarea.insertPlainText(text)
        self.textarea.verticalScrollBar().setValue(1)
        return

    def update(self):
        """Reload previews"""

        self.showText()
        self.values = getWidgetValues(self.widgets)
        timeformat = self.values['time format']
        dateparse = lambda x: pd.datetime.strptime(x, timeformat)
        del self.values['time format']
        del self.values['rowsperfile']
        print (self.values)

        try:
            f = pd.read_csv(self.filename, chunksize=400, error_bad_lines=False,
                        warn_bad_lines=False, date_parser=dateparse)#, **self.values)
        except Exception as e:
            print ('read csv error')
            print (e)
            return
        try:
            df = f.get_chunk()
        except pandas.errors.ParserError:
            print ('parser error')
            df = pd.DataFrame()

        self.previewtable.model.df = df
        self.previewtable.refresh()
        return

    def doImport(self):
        """Do the import"""

        self.update()
        self.df = pd.read_csv(self.filename)#, **self.values)
        self.close()
        return

    def quit(self):
        self.main.destroy()
        return

class BasicDialog(QDialog):
    """Qdialog for table operations interfaces"""
    def __init__(self, parent, df, title=None):

        super(BasicDialog, self).__init__(parent)
        self.parent = parent
        self.df = df
        self.app = self.parent.app
        self.setWindowTitle(title)
        self.createWidgets()
        self.setGeometry(QtCore.QRect(400, 300, 1000, 600))
        self.show()
        return

    def createWidgets(self):
        """Create widgets - override this"""

        cols = list(self.df.columns)

    def createButtons(self, parent):

        bw = self.button_widget = QWidget(parent)
        vbox = QVBoxLayout(bw)
        vbox.setAlignment(QtCore.Qt.AlignTop)
        button = QPushButton("Apply")
        button.clicked.connect(self.apply)
        vbox.addWidget(button)
        button = QPushButton("Copy to sub-table")
        button.clicked.connect(self.copy_to_subtable)
        vbox.addWidget(button)
        button = QPushButton("Copy to clipboard")
        button.clicked.connect(self.copy_to_clipboard)
        vbox.addWidget(button)
        button = QPushButton("Copy to new sheet")
        button.clicked.connect(self.copy_to_sheet)
        vbox.addWidget(button)
        button = QPushButton("Export result")
        button.clicked.connect(self.export)
        vbox.addWidget(button)
        button = QPushButton("Close")
        button.clicked.connect(self.close)
        vbox.addWidget(button)
        return bw

    def apply(self):
        """Override this"""
        return

    def copy_to_subtable(self):
        """Do the operation"""

        df = self.table.model.df
        self.parent.createSubTable(df)
        return

    def copy_to_sheet(self):
        """Copy result to new sheet in app, if available"""

        if self.app == None:
            return
        name, ok = QInputDialog().getText(self, "Enter Sheet Name",
                                             "Name:", QLineEdit.Normal)
        if ok and name:
            self.app.addSheet(name=name, df=self.table.model.df)
        return

    def copy_to_clipboard(self):
        """Copy result to clipboard"""

        df = self.table.model.df
        df.to_clipboard()
        return

    def export(self):
        """export result to file"""

        df = self.table.model.df
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(self,"Export File",
                             "","CSV files (*.csv);;",
                             options=options)
        if not filename:
            return
        if not os.path.splitext(filename)[1] == '.csv':
            filename += '.csv'
        df.to_csv(filename)
        return

    def close(self):
        self.destroy()
        return

class AggregateDialog(BasicDialog):
    """Qdialog with multiple inputs"""
    def __init__(self, parent, df, title='Groupby-Aggregate'):

        BasicDialog.__init__(self, parent, df, title)
        return

    def createWidgets(self):
        """Create widgets"""

        cols = list(self.df.columns)
        funcs = ['sum','mean','size','std','min','max','var']
        vbox = QHBoxLayout(self)
        main = QWidget(self)
        main.setMaximumWidth(300)
        vbox.addWidget(main)

        l = QVBoxLayout(main)
        w = self.groupbyw = QListWidget(main)
        w.setSelectionMode(QAbstractItemView.MultiSelection)
        w.addItems(cols)
        l.addWidget(QLabel('Group by'))
        l.addWidget(w)
        w = self.aggw = QListWidget(main)
        w.setSelectionMode(QAbstractItemView.MultiSelection)
        w.addItems(cols)
        l.addWidget(QLabel('Aggregate on'))
        l.addWidget(w)
        w = self.funcw = QListWidget(main)
        w.setSelectionMode(QAbstractItemView.MultiSelection)
        w.addItems(funcs)
        l.addWidget(QLabel('Functions'))
        l.addWidget(w)

        from . import core
        self.table = core.DataFrameTable(self)
        vbox.addWidget(self.table)
        bf = self.createButtons(self)
        vbox.addWidget(bf)
        return

    def customButtons():
        vbox.addWidget(QLabel('map cols to functions'))
        mapcolsbtn = QCheckBox()
        vbox.addWidget(mapcolsbtn)

    def apply(self):
        """Do the operation"""

        grpcols = [i.text() for i in self.groupbyw.selectedItems()]
        aggcols =[i.text() for i in self.aggw.selectedItems()]
        funcs = [i.text() for i in self.funcw.selectedItems()]
        aggdict = {}

        if len(funcs)==1: funcs=funcs[0]
        for a in aggcols:
            aggdict[a] = funcs

        res = self.df.groupby(grpcols).agg(aggdict).reset_index()
        self.table.model.df = res
        self.table.refresh()
        return

class PivotDialog(BasicDialog):
    """Dialog to pivot table"""
    def __init__(self, parent, df, title='Pivot'):

        BasicDialog.__init__(self, parent, df, title)
        return

    def createWidgets(self):
        """Create widgets"""

        cols = list(self.df.columns)
        funcs = ['sum','mean','size','std','min','max','var']
        vbox = QHBoxLayout(self)
        main = QWidget(self)
        main.setMaximumWidth(300)
        vbox.addWidget(main)

        l = QVBoxLayout(main)
        w = self.columnsw = QListWidget(main)
        w.setSelectionMode(QAbstractItemView.MultiSelection)
        w.addItems(cols)
        l.addWidget(QLabel('Columns'))
        l.addWidget(w)
        w = self.valuesw = QListWidget(main)
        w.setSelectionMode(QAbstractItemView.MultiSelection)
        w.addItems(cols)
        l.addWidget(QLabel('Values'))
        l.addWidget(w)
        w = self.idxw = QListWidget(main)
        w.addItems(cols)
        l.addWidget(QLabel('Index'))
        l.addWidget(w)
        w = self.aggw = QListWidget(main)
        w.addItems(funcs)
        l.addWidget(QLabel('Aggregate function'))
        l.addWidget(w)

        from . import core
        self.table = core.DataFrameTable(self)
        vbox.addWidget(self.table)
        bf = self.createButtons(self)
        vbox.addWidget(bf)

    def apply(self):
        """Do the operation"""

        cols = [i.text() for i in self.columnsw.selectedItems()]
        vals =[i.text() for i in self.valuesw.selectedItems()]
        idx = self.idxw.selectedItems()[0].text()
        aggfuncs = [i.text() for i in self.aggw.selectedItems()]
        res = pd.pivot_table(self.df, index=idx, columns=cols, values=vals, aggfunc=aggfuncs)
        print (res.columns)
        if util.check_multiindex(res.columns) == 1:
            res.columns = res.columns.get_level_values(2)

        self.table.model.df = res
        self.table.refresh()
        return

class MeltDialog(BasicDialog):
    """Dialog to melt table"""
    def __init__(self, parent, df, title='Melt'):

        BasicDialog.__init__(self, parent, df, title)
        return

    def createWidgets(self):
        """Create widgets"""

        cols = list(self.df.columns)
        funcs = ['sum','mean','size','std','min','max','var']
        vbox = QHBoxLayout(self)
        main = QWidget(self)
        main.setMaximumWidth(300)
        vbox.addWidget(main)

        l = QVBoxLayout(main)
        w = self.idvarsw = QListWidget(main)
        w.setSelectionMode(QAbstractItemView.MultiSelection)
        w.addItems(cols)
        l.addWidget(QLabel('ID vars'))
        l.addWidget(w)
        w = self.valuevarsw = QListWidget(main)
        w.setSelectionMode(QAbstractItemView.MultiSelection)
        w.addItems(cols)
        l.addWidget(QLabel('Value vars'))
        l.addWidget(w)
        w = self.varnamew = QLineEdit('var')
        l.addWidget(QLabel('Var name'))
        l.addWidget(w)

        from . import core
        self.table = core.DataFrameTable(self)
        vbox.addWidget(self.table)
        bf = self.createButtons(self)
        vbox.addWidget(bf)
        return

    def apply(self):
        """Do the operation"""

        idvars = [i.text() for i in self.idvarsw.selectedItems()]
        value_vars =[i.text() for i in self.valuevarsw .selectedItems()]
        varname = self.varnamew.text()
        res = pd.melt(self.df, idvars, value_vars, varname)

        self.table.model.df = res
        self.table.refresh()
        return

class MergeDialog(BasicDialog):
    """Dialog to melt table"""
    def __init__(self, parent, df, title='Merge Tables'):

        BasicDialog.__init__(self, parent, df, title)
        return

    def createWidgets(self):
        """Create widgets"""

        if hasattr(self.parent, 'subtable'):
            self.df2 = self.parent.subtable.table.model.df
            cols2 = self.df2.columns
        else:
            self.df2 = None
            cols2 = []
        cols = list(self.df.columns)
        ops = ['merge','concat']
        how = ['inner','outer']
        hbox = QHBoxLayout(self)
        main = QWidget(self)
        main.setMaximumWidth(300)
        hbox.addWidget(main)

        l = QVBoxLayout(main)
        w = self.ops_w = QComboBox(main)
        w.addItems(ops)
        l.addWidget(QLabel('Operation'))
        l.addWidget(w)
        w = self.lefton_w = QListWidget(main)
        w.setSelectionMode(QAbstractItemView.MultiSelection)
        w.addItems(cols)
        l.addWidget(QLabel('Left on'))
        l.addWidget(w)
        w = self.righton_w = QListWidget(main)
        w.setSelectionMode(QAbstractItemView.MultiSelection)
        w.addItems(cols2)
        l.addWidget(QLabel('Right on'))
        l.addWidget(w)

        w = self.how_w = QComboBox(main)
        w.addItems(how)
        l.addWidget(QLabel('How'))
        l.addWidget(w)

        w = self.left_suffw = QLineEdit('_1')
        l.addWidget(QLabel('Left suffix'))
        l.addWidget(w)
        w = self.right_suffw = QLineEdit('_2')
        l.addWidget(QLabel('Right suffix'))
        l.addWidget(w)

        '''
        tableswidget = QWidget(self)
        l = QVBoxLayout(tableswidget)
        self.table1 = app.DataFrameTable(tableswidget, self.df)
        self.table2 = app.DataFrameTable(tableswidget, subdf)
        l.addWidget(self.table1)
        l.addWidget(self.table2)
        hbox.addWidget(tableswidget)'''
        from . import core
        self.table = core.DataFrameTable(self)
        hbox.addWidget(self.table)
        bf = self.createButtons(self)
        hbox.addWidget(bf)
        return

    def apply(self):
        """Do the operation"""

        lefton = [i.text() for i in self.lefton_w.selectedItems()]
        righton = [i.text() for i in self.righton_w.selectedItems()]
        print (lefton)
        res = pd.merge(self.df, self.df2,
                            left_on=lefton,
                            right_on=righton,
                            suffixes=(self.left_suffw .text(),self.right_suffw.text())
                            )

        self.table.model.df = res
        self.table.refresh()
        return

class ConvertTypesDialog(BasicDialog):
    """Dialog to melt table"""
    def __init__(self, parent, df, title='Convert types'):

        BasicDialog.__init__(self, parent, df, title)
        return

    def createButtons(self, parent):

        bw = self.button_widget = QWidget(parent)
        vbox = QVBoxLayout(bw)
        vbox.setAlignment(QtCore.Qt.AlignTop)
        button = QPushButton("Apply")
        button.clicked.connect(self.apply)
        vbox.addWidget(button)
        button = QPushButton("Copy to new sheet")
        button.clicked.connect(self.copy_to_sheet)
        vbox.addWidget(button)
        button = QPushButton("Close")
        button.clicked.connect(self.close)
        vbox.addWidget(button)
        return bw

    def createWidgets(self):
        """Create widgets"""

        cols = list(self.df.columns)

        vbox = QHBoxLayout(self)
        main = QWidget(self)
        main.setMaximumWidth(300)
        vbox.addWidget(main)

        res = []
        for col in self.df.columns:
            res.append([col,str(self.df[col].dtype),''])
        cols = ['name','type','convert']
        info = pd.DataFrame(res, columns=cols)

        from . import core
        self.table = core.DataFrameTable(self, info)
        vbox.addWidget(self.table)
        bf = self.createButtons(self)
        vbox.addWidget(bf)
        return

    def apply(self):
        """Do the operation"""

        idvars = [i.text() for i in self.idvarsw.selectedItems()]
        value_vars =[i.text() for i in self.valuevarsw .selectedItems()]
        varname = self.varnamew.text()
        res = pd.melt(self.df, idvars, value_vars, varname)

        self.table.model.df = res
        self.table.refresh()
        return

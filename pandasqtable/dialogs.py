#!/usr/bin/env python
"""
    Implements some dialog utilities for pandasqtable
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
import os, types
import string, copy
from collections import OrderedDict
try:
    import configparser
except:
    import ConfigParser as configparser
from PySide2 import QtCore, QtGui
from PySide2.QtCore import QObject
from PySide2.QtWidgets import *
from PySide2.QtGui import *

def dialogFromOptions(parent, opts, sections=None,
                      sticky='news', wrap=2, section_wrap=5):
    """Get Qt widgets dialog from a dictionary of options"""

    sizepolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    sizepolicy.setHorizontalStretch(0)
    sizepolicy.setVerticalStretch(0)

    style = '''
    QLabel {
        font-size: 12px;
    }
    QWidget {
        max-width: 200px;
        min-width: 60px;
        font-size: 14px;
    }

    '''

    if sections == None:
        sections = {'options': opts.keys()}

    widgets = {}
    dialog = QWidget(parent)
    dialog.setSizePolicy(sizepolicy)

    l = QGridLayout(dialog)
    l.setSpacing(2)

    scol=1
    for s in sections:
        row=1
        col=1
        f = QWidget()
        f.resize(50,100)
        f.sizeHint()
        l.addWidget(f,1,scol)
        gl = QGridLayout(f)
        gl.setSpacing(4)
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
                w.setCurrentIndex(1)
            elif t == 'entry':
                w = QLineEdit()
                w.setText(str(val))
                #if type(val) is int:
                #    w.setValidator(QIntValidator(0, 100, this))
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
                w.setCurrentIndex(5)
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
        if scol > section_wrap:
            scol=1
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

class TextDialog(QDialog):
    """Text edit dialog"""
    def __init__(self, parent, text='', title='Text'):
        super(TextDialog, self).__init__(parent)
        self.setMinimumSize(440, 300)
        self.setWindowTitle(title)
        vbox = QVBoxLayout(self)
        b = self.textbox = QPlainTextEdit(self)
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
        self.setMinimumSize(440, 300)
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
    """Provides a frame for figure canvas and MPL settings"""

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
        self.show()
        return

    def createWidgets(self):
        delimiters = [',',r'\t',' ',';','/','&','|','^','+','-']
        encodings = ['utf-8','ascii','iso8859_15','cp037','cp1252','big5','euc_jp']
        timeformats = ['infer','%d/%m/%Y','%Y/%m/%d','%Y/%d/%m',
                        '%Y-%m-%d %H:%M:%S','%Y-%m-%d %H:%M',
                        '%d-%m-%Y %H:%M:%S','%d-%m-%Y %H:%M']
        grps = {'formats':['delimiter','decimal','comment'],
                'data':['header','skiprows','index_col','skipinitialspace',
                        'skip_blank_lines','parse_dates','time format','encoding','names'],
                'other':['rowsperfile']}
        grps = OrderedDict(sorted(grps.items()))
        opts = self.opts = {'delimiter':{'type':'combobox','default':',',
                        'items':delimiters, 'tooltip':'seperator'},
                     'header':{'type':'entry','default':0,'label':'header',
                               'tooltip':'position of column header'},
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

        optsframe, widgets = dialogFromOptions(self, opts, grps, wrap=2, section_wrap=1)
        layout = QGridLayout()
        layout.setColumnStretch(1,2)
        layout.addWidget(optsframe,1,1)
        optsframe.setMaximumWidth(250)
        #optsframe.resize(50,300)
        bf = self.createButtons(optsframe)
        layout.addWidget(bf,2,1)

        main = QSplitter(self)
        main.setOrientation(QtCore.Qt.Vertical)
        layout.addWidget(main,1,2,2,1)

        self.textarea = QPlainTextEdit(main)
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
        self.textpreview.delete('1.0', END)
        self.textpreview.insert('1.0', text)
        return

    def update(self):
        """Reload previews"""

        kwds = {}
        other = ['rowsperfile','time format']
        for i in self.opts:
            if i in other:
                continue
            try:
                val = self.tkvars[i].get()
            except:
                val=None
            if val == '':
                val=None
            if self.opts[i]['type'] == 'checkbutton':
                val = bool(val)
            elif type(self.opts[i]['default']) != int:
                try:
                    val=int(val)
                except:
                    pass
            kwds[i] = val
        self.kwds = kwds
        timeformat = self.tkvars['time format'].get()
        dateparse = lambda x: pd.datetime.strptime(x, timeformat)
        self.showText()
        try:
            f = pd.read_csv(self.filename, chunksize=400, error_bad_lines=False,
                        warn_bad_lines=False, date_parser=dateparse, **kwds)
        except Exception as e:
            print ('read csv error')
            print (e)
            return
        try:
            df = f.get_chunk()
        except pandas.errors.ParserError:
            print ('parser error')
            df = pd.DataFrame()

        model = TableModel(dataframe=df)
        self.previewtable.updateModel(model)
        self.previewtable.showIndex()
        self.previewtable.redraw()
        return

    def doImport(self):
        """Do the import"""

        self.update()
        self.df = pd.read_csv(self.filename, **self.kwds)
        self.quit()
        return

    def quit(self):
        self.main.destroy()
        return

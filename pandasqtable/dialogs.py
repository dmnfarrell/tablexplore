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
                      sticky='news',  layout='horizontal'):
    """Get Qt widgets dialog from a dictionary of options"""

    sizepolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    sizepolicy.setHorizontalStretch(0)
    sizepolicy.setVerticalStretch(0)

    if sections == None:
        sections = {'options': opts.keys()}

    widgets = {}
    dialog = QWidget(parent)
    dialog.setSizePolicy(sizepolicy)
    if layout == 'horizontal':
        l = QHBoxLayout(dialog)
    else:
        l = QVBoxLayout(dialog)
    for s in sections:
        f = QWidget()
        f.resize(50,100)
        f.sizeHint()
        l.addWidget(f)
        #vb = QVBoxLayout(f)
        gl = QGridLayout(f)
        gl.setSpacing(4)
        i=0
        for o in sections[s]:
            label = o
            opt = opts[o]
            if label in opt:
                label = opt['label']
            t = opt['type']
            gl.addWidget(QLabel(label),i,1)
            if t == 'combobox':
                w = QComboBox()
                w.addItems(opt['items'])
            elif t == 'entry':
                w = QLineEdit()
            elif t == 'slider':
                w = QSlider(QtCore.Qt.Horizontal)
                s,e = opt['range']
                w.setTickInterval(opt['interval'])
                w.setSingleStep(float(s-e)/10)
                w.setMinimum(s)
                w.setMaximum(e)
                w.setTickPosition(QSlider.TicksBelow)
                #w.resize(10,10)
            elif t == 'spinbox':
                w = QSpinBox()
            elif t == 'checkbox':
                w = QCheckBox()
            elif t == 'font':
                w = QFontComboBox()
                w.resize(w.sizeHint())
            gl.addWidget(w,i,2)
            widgets[o] = w
            i+=1

    return dialog, widgets

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
        self.setGeometry(QtCore.QRect(100, 50, 800, 600))
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

        optsframe, widgets = dialogFromOptions(self, opts, grps,
                                    layout='vertical')
        layout = QGridLayout()
        layout.setColumnStretch(2, 1)

        layout.addWidget(optsframe,1,1)
        optsframe.resize(50,300)
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

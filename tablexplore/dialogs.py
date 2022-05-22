#!/usr/bin/env python
"""
    Implements some dialog utilities for tablexplore
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
import traceback
import string, copy
from collections import OrderedDict
import pandas as pd
try:
    import configparser
except:
    import ConfigParser as configparser
from .qt import *
from . import util, core

module_path = os.path.dirname(os.path.abspath(__file__))
iconpath = os.path.join(module_path, 'icons')

def getName(parent, current='', txt='Enter value'):
    """Wrapper for text inpuit dialog"""

    name, ok = QInputDialog().getText(parent, txt,
                                     "Name:", QLineEdit.Normal, text=current)
    if ok:
        return name

def showMessage(parent, msg, type='error'):
    """Show an error message"""

    QMessageBox.information(parent, type, msg)
    return

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
            font-size: 14px;
        }
        QPlainTextEdit {
            max-height: 80px;
        }
        QComboBox {
            combobox-popup: 0;
            max-height: 30px;
            max-width: 150px;
        }
        '''

    if sections == None:
        sections = {'options': opts.keys()}

    widgets = {}
    dialog = QWidget(parent)
    dialog.setSizePolicy(sizepolicy)

    l = QGridLayout(dialog)
    l.setSpacing(1)
    l.setAlignment(QtCore.Qt.AlignTop)
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
            lbl.setMinimumWidth(150)
            gl.addWidget(lbl,row,col)
            lbl.setStyleSheet(style)
            if t == 'combobox':
                w = QComboBox()
                w.addItems(opt['items'])
                index = w.findText(val)
                if index != -1:
                    w.setCurrentIndex(index)
                if 'editable' in opt:
                     w.setEditable(True)
                if 'width' in opt:
                    w.setMinimumWidth(opt['width'])
                    w.resize(opt['width'], 20)
                w.view().setMinimumWidth(120)
                w.setMaxVisibleItems(12)
            elif t == 'list':
                w = QListWidget()
                w.setSelectionMode(QAbstractItemView.MultiSelection)
                w.addItems(opt['items'])
            elif t == 'entry':
                w = QLineEdit()
                w.setText(str(val))
                if 'width' in opt:
                    w.setMaximumWidth(opt['width'])
                    w.resize(opt['width'], 20)
            elif t == 'textarea':
                w = QPlainTextEdit()
                #w.setSizePolicy(sizepolicy)
                w.insertPlainText(str(val))
                w.setMaximumHeight(100)
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
                if 'range' in opt:
                    min, max = opt['range']
                    min = int(min)
                    max = int(max)
                    w.setRange(min,max)
                    w.setMaximum(max)
                    w.setMinimum(min)
                if 'interval' in opt:
                    w.setSingleStep(opt['interval'])
            elif t == 'doublespinbox':
                w = QDoubleSpinBox()
                w.setValue(val)
                if 'range' in opt:
                    min, max = opt['range']
                    w.setRange(min,max)
                    w.setMinimum(min)
                if 'interval' in opt:
                    w.setSingleStep(opt['interval'])
            elif t == 'checkbox':
                w = QCheckBox()
                w.setChecked(val)
            elif t == 'font':
                w = QFontComboBox()
                index = w.findText(val)
                #w.resize(w.sizeHint())
                w.setCurrentIndex(index)
            elif t == 'dial':
                w = QDial()
                if 'range' in opt:
                    min, max = opt['range']
                    w.setMinimum(min)
                    w.setMaximum(max)
                w.setValue(val)
            elif t == 'colorbutton':
                w = ColorButton()
                w.setColor(val)
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

def getWidgetValue(w):
    """Get value from any kind of widget"""

    val = None
    if type(w) is QLineEdit:
        val = w.text()
    elif type(w) is QPlainTextEdit:
        val = w.toPlainText()
    elif type(w) is QComboBox or type(w) is QFontComboBox:
        val = w.currentText()
    elif type(w) is QListWidget:
        val = [i.text() for i in w.selectedItems()]
    elif type(w) is QCheckBox:
        val = w.isChecked()
    elif type(w) is QSlider:
        val = w.value()
    elif type(w) in [QSpinBox,QDoubleSpinBox]:
        val = w.value()
    elif type(w) is ColorButton:
        val = w.color()
    return val

def getWidgetValues(widgets):
    """Get values back from a set of widgets"""

    kwds = {}
    for i in widgets:
        val = None
        if i in widgets:
            w = widgets[i]
            val = getWidgetValue(w)
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
                w.clear()
                w.insertPlainText(str(val))
            elif type(w) is QComboBox or type(w) is QFontComboBox:
                index = w.findText(val)
                w.setCurrentIndex(index)
            elif type(w) is QCheckBox:
                w.setChecked(val)
            elif type(w) is QSlider:
                w.setValue(val)
            elif type(w) == QSpinBox:
                w.setValue(int(val))
            elif type(w) == QDoubleSpinBox:
                w.setValue(val)
    return

def addToolBarItems(toolbar, parent, items):
    """Populate toolbar from dict of items"""

    for i in items:
        if 'file' in items[i]:
            iconfile = os.path.join(iconpath,items[i]['file']+'.png')
            icon = QIcon(iconfile)
        else:
            icon = QIcon.fromTheme(items[i]['icon'])
        btn = QAction(icon, i, parent)
        if 'action' in items[i]:
            btn.triggered.connect(items[i]['action'])
        if 'shortcut' in items[i]:
            btn.setShortcut(QKeySequence(items[i]['shortcut']))
        if 'checkable' in items[i]:
            btn.setCheckable(True)
        toolbar.addAction(btn)
    return toolbar

class ColorButton(QPushButton):
    '''
    Custom Qt Widget to show a chosen color.

    Left-clicking the button shows the color-chooser, while
    right-clicking resets the color to None (no-color).
    '''

    colorChanged = Signal(object)

    def __init__(self, *args, color=None, **kwargs):
        super(ColorButton, self).__init__(*args, **kwargs)

        self._color = None
        self._default = color
        self.pressed.connect(self.onColorPicker)

        # Set the initial/default state.
        self.setColor(self._default)

    def setColor(self, color):

        if color != self._color:
            self._color = color
            self.colorChanged.emit(color)

        if self._color:
            self.setStyleSheet("background-color: %s;" % self._color)
        else:
            self.setStyleSheet("")    
        return

    def color(self):
        return self._color

    def onColorPicker(self):
        '''
        Show color-picker dialog to select color.
        Qt will use the native dialog by default.
        '''
        dlg = QColorDialog(self)
        if self._color:
            dlg.setCurrentColor(QColor(self._color))

        if dlg.exec_():
            self.setColor(dlg.currentColor().name())

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.RightButton:
            self.setColor(self._default)

        return super(ColorButton, self).mousePressEvent(e)

class ProgressWidget(QDialog):
    """Progress widget class"""
    def __init__(self, parent=None, label=''):
        super(ProgressWidget, self).__init__(parent)
        layout = QVBoxLayout(self)
        self.setWindowTitle(label)
        self.setMinimumSize(400,100)
        self.setGeometry(
                QStyle.alignedRect(
                    QtCore.Qt.LeftToRight,
                    QtCore.Qt.AlignCenter,
                    self.size(),
                    QGuiApplication.primaryScreen().availableGeometry(),
                ))
        self.setMaximumHeight(100)
        self.label = QLabel(label)
        layout.addWidget(self.label)
        # Create a progress bar
        self.progressbar = QProgressBar(self)
        layout.addWidget(self.progressbar)
        self.progressbar.setGeometry(30, 40, 400, 200)

        return

#https://www.learnpyqt.com/courses/concurrent-execution/multithreading-pyqt-applications-qthreadpool/
class Worker(QtCore.QRunnable):
    """Worker thread for running background tasks."""

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.kwargs['progress_callback'] = self.signals.progress

    @Slot()
    def run(self):
        try:
            result = self.fn(
                *self.args, **self.kwargs,
            )
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

class WorkerSignals(QtCore.QObject):
    """
    Defines the signals available from a running worker thread.
    Supported signals are:
    finished
        No data
    error
        `tuple` (exctype, value, traceback.format_exc() )
    result
        `object` data returned from processing, anything
    """
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(str)

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
    def __init__(self, parent, options=None, title='Input', width=400, height=200):
        super(MultipleInputDialog, self).__init__(parent)
        self.values = None
        self.accepted = False
        self.setMinimumSize(width, height)
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

        super(ImportDialog, self).__init__(parent)
        self.parent = parent
        self.filename = filename
        self.df = None
        self.setGeometry(QtCore.QRect(250, 250, 900, 600))
        self.setGeometry(
                QStyle.alignedRect(
                    QtCore.Qt.LeftToRight,
                    QtCore.Qt.AlignCenter,
                    self.size(),
                    QGuiApplication.primaryScreen().availableGeometry(),
                ))
        self.setWindowTitle('Import File')
        self.createWidgets()
        self.update()
        self.show()
        return

    def createWidgets(self):
        """Create widgets"""

        delimiters = [',',r'\t',' ','\s+',';','/','&','|','^','+','-']
        encodings = ['utf-8','ascii','latin-1','iso8859_15','cp037','cp1252','big5','euc_jp',
                     'koi8_r','mac_latin2','utf_32']
        timeformats = ['infer','%d/%m/%Y','%Y/%m/%d','%Y/%d/%m',
                        '%Y-%m-%d %H:%M:%S','%Y-%m-%d %H:%M',
                        '%d-%m-%Y %H:%M:%S','%d-%m-%Y %H:%M']
        grps = {'formats':['sep','decimal','comment'],
                'data':['skiprows','skipinitialspace',
                        'skip_blank_lines','parse_dates','encoding','time format'],
                'other':['rowsperfile']}
        grps = OrderedDict(sorted(grps.items()))
        opts = self.opts = {'sep':{'type':'combobox','default':',','editable':True,
                        'items':delimiters, 'tooltip':'seperator'},
                     #'header':{'type':'entry','default':0,'label':'header',
                     #          'tooltip':'position of column header'},
                     'decimal':{'type':'combobox','default':'.','items':['.',','],
                                'tooltip':'decimal point symbol'},
                     'comment':{'type':'entry','default':'#','label':'comment',
                                'tooltip':'comment symbol'},
                     'skipinitialspace':{'type':'checkbox','default':0,'label':'skip initial space',
                                'tooltip':'skip initial space'},
                     'skiprows':{'type':'spinbox','default':0,'label':'skiprows',
                                'tooltip':'rows to skip'},
                     'skip_blank_lines':  {'type':'checkbox','default':0,'label':'skip blank lines',
                                'tooltip':'do not use blank lines'},
                     'parse_dates':  {'type':'checkbox','default':1,'label':'parse dates',
                                'tooltip':'try to parse date/time columns'},
                     'time format': {'type':'combobox','default':'','items':timeformats,
                                'tooltip':'date/time format'},
                     'encoding':{'type':'combobox','default':'utf-8','items':encodings,
                                'tooltip':'file encoding'},
                     #'prefix':{'type':'entry','default':None,'label':'prefix',
                     #           'tooltip':''}
                     'rowsperfile':{'type':'spinbox','default':0,'label':'rows per file',
                                'tooltip':'rows to read'}
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
        main.addWidget(self.textarea)

        t = self.previewtable = core.DataFrameTable(main, font=core.FONT)
        t.mode = 'locked'
        main.addWidget(t)

        t = self.typestable = core.DataFrameTable(main)
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

    def showText(self, encoding='utf-8'):
        """Show text contents"""

        self.textarea.clear()
        try:
            file = open(self.filename, 'r', encoding=encoding)
            for i in range(100):
                 line = file.readline()
                 self.textarea.insertPlainText(line)
            self.textarea.verticalScrollBar().setValue(1)
        except Exception as e:
            print(e)
            self.textarea.insertPlainText(str(e)+'\n')
            self.textarea.insertPlainText('try another encoding?')
        return

    def update(self):
        """Reload previews"""

        self.values = getWidgetValues(self.widgets)
        enc = self.values['encoding']
        self.showText(enc)
        timeformat = self.values['time format']
        if timeformat == 'infer':
            dateparse=None
        else:
            dateparse = lambda x: pd.datetime.strptime(x, timeformat)

        del self.values['time format']
        del self.values['rowsperfile']

        for k in self.values:
            if self.values[k] == '':
                self.values[k] = None
        try:
            f = pd.read_csv(self.filename, chunksize=400, on_bad_lines='skip',
                            date_parser=dateparse, **self.values)
        except Exception as e:
            print ('read csv error')
            print (e)
            return
        try:
            df = f.get_chunk()
        except UnicodeDecodeError:
            print ('unicode error')
            df = pd.DataFrame()
        except pd.errors.ParserError:
            print ('parser error')
            df = pd.DataFrame()

        self.previewtable.model.df = df
        self.previewtable.refresh()

        #update types table
        tdf = df.dtypes.to_frame(name='dtype').reset_index()
        tdf=tdf.rename(columns={'index':'name'})
        tdf['dtype'] = tdf.dtype.astype(str)
        self.typestable.model.df = tdf
        self.typestable.refresh()
        items = ['int64','float64','object']
        self.typestable.setItemDelegateForColumn(1,ComboDelegate(self.typestable, items))
        self.typestable.setEditTriggers(QAbstractItemView.CurrentChanged)
        return

    def doImport(self):
        """Do the import"""

        #self.update()
        #get types if changed?
        tf = self.typestable.model.df
        dtypes = dict(zip(tf.name, tf.dtype))
        #print (dtypes)
        #dtmap = {'int32':int32,'float32':float64}
        #for i in dtypes:
        #    dtypes[i] = dtmap[i]
        try:
            self.df = pd.read_csv(self.filename, dtype=dtypes, **self.values)
        except:
            self.df = pd.read_csv(self.filename)
        self.close()
        return

    #def closeEvent(self, event):
    #    self.accepted = None

    def quit(self):
        self.accepted = None
        self.close()
        return

class ComboDelegate(QItemDelegate):
    """
    A delegate to add QComboBox in every cell of the given column
    """

    def __init__(self, parent, items):
        super(ComboDelegate, self).__init__(parent)
        self.parent = parent
        self.items = items

    def createEditor(self, parent, option, index):
        self.combobox = QComboBox(parent)
        self.combobox.addItems(self.items)
        self.combobox.currentIndexChanged.connect(self.currentIndexChanged)
        return self.combobox

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.EditRole)
        num = self.items.index(value)
        editor.setCurrentIndex(num)

    def setModelData(self, combo, model, index):
        comboIndex = combo.currentIndex()
        text=self.items[comboIndex]
        model.setData(index, text)

    @Slot()
    def currentIndexChanged(self):
        self.commitData.emit(self.sender())

class SimpleDialog(QDialog):
    """Qdialog for table operations interfaces"""
    def __init__(self, parent, title=None):

        super(SimpleDialog, self).__init__(parent)
        self.parent = parent
        self.setWindowTitle(title)
        self.setGeometry(QtCore.QRect(400, 300, 1000, 600))
        self.resize(500, 200)
        self.layout = QVBoxLayout(self)
        self.show()
        return

    def createButtons(self):
        """Create buttons"""
        self.button_box = QDialogButtonBox(
                    QDialogButtonBox.Cancel|QDialogButtonBox.Ok ,
                    QtCore.Qt.Horizontal,
                    self
        )
        return

class BasicDialog(QDialog):
    """Qdialog for table operations interfaces"""
    def __init__(self, parent, df, title=None, app=None):

        super(BasicDialog, self).__init__(parent)
        self.parent = parent
        self.df = df
        if app != None:
            self.app = app
        else:
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
        if hasattr(self.parent, 'subtable'):
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
        self.parent.showSubTable(df)
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

        self.table = core.DataFrameTable(self, font=core.FONT)
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
        #w.setSelectionMode(QAbstractItemView.MultiSelection)
        w.addItems(cols)
        l.addWidget(QLabel('Columns'))
        l.addWidget(w)
        w = self.idxw = QListWidget(main)
        #w.setSelectionMode(QAbstractItemView.MultiSelection)
        w.addItems(cols)
        l.addWidget(QLabel('Index'))
        l.addWidget(w)
        w = self.valuesw = QListWidget(main)
        w.setSelectionMode(QAbstractItemView.MultiSelection)
        w.addItems(cols)
        l.addWidget(QLabel('Values'))
        l.addWidget(w)
        w = self.aggw = QListWidget(main)
        w.addItems(funcs)
        l.addWidget(QLabel('Aggregate function'))
        l.addWidget(w)

        self.table = core.DataFrameTable(self, font=core.FONT)
        vbox.addWidget(self.table)
        bf = self.createButtons(self)
        vbox.addWidget(bf)

    def apply(self):
        """Do the operation"""

        cols = [i.text() for i in self.columnsw.selectedItems()]
        vals =[i.text() for i in self.valuesw.selectedItems()]
        idx = [i.text() for i in self.idxw.selectedItems()]
        aggfuncs = [i.text() for i in self.aggw.selectedItems()]
        res = pd.pivot_table(self.df, index=idx, columns=cols, values=vals, aggfunc=aggfuncs)
        names = res.index.names
        #res = res.reset_index(col_level=2)
        #print (res)
        if util.check_multiindex(res.columns) == 1:
            l = res.columns.nlevels
            res.columns = res.columns.get_level_values(l-1)

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

        self.table = core.DataFrameTable(self, font=core.FONT)
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
    def __init__(self, parent, df, df2=None, title='Merge Tables', app=None):

        self.df2 = df2
        BasicDialog.__init__(self, parent, df, title, app)
        return

    def createWidgets(self):
        """Create widgets"""

        if self.df2 is None:
            if hasattr(self.parent, 'subtable') and self.parent.subtable != None:
                self.df2 = self.parent.subtable.table.model.df
        try:
            cols2 = self.df2.columns
        except:
            cols2 = []
        cols = list(self.df.columns)
        ops = ['merge','concat']
        how = ['inner','outer','left','right']
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

        w = self.leftindex_w = QCheckBox(main)
        w.setChecked(False)
        l.addWidget(QLabel('Use left index'))
        l.addWidget(w)
        w = self.rightindex_w = QCheckBox(main)
        w.setChecked(False)
        l.addWidget(QLabel('Use right index'))
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

        self.table = core.DataFrameTable(self, font=core.FONT)
        hbox.addWidget(self.table)
        bf = self.createButtons(self)
        hbox.addWidget(bf)
        return

    def updateColumns(self):

        #self.df2 =
        cols2 = self.df2.columns
        #w = self.righton_w
        #w.clear()
        #w.addItems(cols2)
        return

    def apply(self):
        """Do the operation"""

        left_index = self.leftindex_w.isChecked()
        right_index = self.rightindex_w.isChecked()
        if left_index == True:
            lefton = None
        else:
            lefton = [i.text() for i in self.lefton_w.selectedItems()]
        if right_index == True:
            righton = None
        else:
            righton = [i.text() for i in self.righton_w.selectedItems()]
        how = self.how_w.currentText()
        op = self.ops_w.currentText()
        if op == 'merge':
            try:
                res = pd.merge(self.df, self.df2,
                                left_on=lefton,
                                right_on=righton,
                                left_index=left_index,
                                right_index=right_index,
                                how=how,
                                suffixes=(self.left_suffw .text(),self.right_suffw.text())
                                )
            except Exception as e:
                showMessage(self, str(e))
        else:
            res = pd.concat([self.df, self.df2])
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

        self.table = core.DataFrameTable(self, info, font=core.FONT)
        types = ['int','float','categorical']

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

class Renamer():
    def __init__(self):
        self.d = dict()

    def __call__(self, x):
        if x not in self.d:
            self.d[x] = 0
            return x
        else:
            self.d[x] += 1
            return "%s_%d" % (x, self.d[x])

class ManageColumnsDialog(BasicDialog):
    """Qdialog for column re-arranging"""
    def __init__(self, parent, df, title='Manage Columns', app=None):

        BasicDialog.__init__(self, parent, df, title)
        self.table = self.parent.table
        self.setGeometry(QtCore.QRect(400, 300, 600, 600))
        self.checknumeric()
        return

    def createWidgets(self):
        """Create widgets - override this"""

        cols = list(self.df.columns)
        vbox = QHBoxLayout(self)
        main = QWidget(self)
        main.setMaximumWidth(250)
        vbox.addWidget(main)
        w = self.cols_w = QListWidget()
        w.setDragDropMode(QAbstractItemView.InternalMove)
        w.setSelectionMode(QAbstractItemView.MultiSelection)
        #w.currentItemChanged.connect(self.update)
        w.addItems(cols)
        vbox.addWidget(w)
        bf = self.createButtons(self)
        vbox.addWidget(bf)
        return

    def createButtons(self, parent):

        bw = self.button_widget = QWidget(parent)
        vbox = QVBoxLayout(bw)
        vbox.setAlignment(QtCore.Qt.AlignTop)
        button = QPushButton("Delete Selected")
        button.clicked.connect(self.delete)
        vbox.addWidget(button)
        button = QPushButton("Update")
        button.clicked.connect(self.update)
        vbox.addWidget(button)
        button = QPushButton("Sort Columns")
        button.clicked.connect(self.sort)
        vbox.addWidget(button)
        button = QPushButton("De-Duplicate")
        button.clicked.connect(self.deduplicate)
        vbox.addWidget(button)
        button = QPushButton("Undo")
        button.clicked.connect(self.undo)
        vbox.addWidget(button)
        button = QPushButton("Close")
        button.clicked.connect(self.close)
        vbox.addWidget(button)
        return bw

    def update(self):
        """Update list"""

        self.cols_w.clear()
        self.cols_w.addItems(self.table.model.df.columns)
        return

    def delete(self):

        self.table.storeCurrent()
        names = [i.text() for i in self.cols_w.selectedItems()]
        df = self.table.model.df
        self.table.model.df = df.drop(columns=names)
        self.table.refresh()
        self.update()
        return

    def sort(self):

        df=self.table.model.df
        cols = df.columns
        self.table.model.df = df[sorted(cols)]
        self.update()
        self.table.refresh()
        return

    def deduplicate(self):
        """Rename duplicate column names"""

        self.table.storeCurrent()
        df = self.table.model.df
        cols = df.columns
        if len(df.columns) == len(set(df.columns)) is True:
            return
        self.table.model.df = df.rename(columns=Renamer())
        self.table.refresh()
        self.update()
        return

    def checknumeric(self):
        """Check if any cols numeric"""

        df = self.table.model.df
        cols = df.columns
        f=False
        for c in cols:
            if type(c) in [float,int]:
                f=True
        if f is True:
            reply = QMessageBox.question(self, 'Convert?',
                                 'Some columns are numeric. Convert to string?',
                                  QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.convert()
        return

    def convert(self):

        self.table.storeCurrent()
        df = self.table.model.df
        self.table.model.df.columns = df.columns.astype(str)
        self.table.refresh()
        self.update()
        return

    def undo(self):

        self.table.undo()
        self.cols_w.clear()
        self.cols_w.addItems(self.table.model.df.columns)

class PreferencesDialog(QDialog):
    """Preferences dialog from config parser options"""

    def __init__(self, parent, options={}):

        super(PreferencesDialog, self).__init__(parent)
        self.parent = parent
        self.setWindowTitle('Preferences')
        self.resize(400, 200)
        self.setGeometry(QtCore.QRect(300,300, 600, 200))
        self.setMaximumWidth(600)
        self.setMaximumHeight(300)
        self.createWidgets(options)
        self.show()
        return

    def createWidgets(self, options):
        """create widgets"""

        import pylab as plt

        colormaps = sorted(m for m in plt.cm.datad if not m.endswith("_r"))
        timeformats = ['%m/%d/%Y','%d/%m/%Y','%d/%m/%y',
                '%Y/%m/%d','%y/%m/%d','%Y/%d/%m',
                '%d-%b-%Y','%b-%d-%Y',
                '%Y-%m-%d %H:%M:%S','%Y-%m-%d %H:%M',
                '%d-%m-%Y %H:%M:%S','%d-%m-%Y %H:%M',
                '%Y','%m','%d','%b']
        plotstyles = ['','default', 'classic', 'fivethirtyeight',
                     'seaborn-pastel','seaborn-whitegrid', 'ggplot','bmh',
                     'grayscale','dark_background']
        themes = QStyleFactory.keys() + ['dark','light']

        self.opts = {
                #'rowheight':{'type':'spinbox','default':18,'range':(5,50),'label':'Row height'},
                'ALIGNMENT':{'type':'combobox','default':'w','items':['left','right','center'],'label':'Text Align'},
                'BGCOLOR':{'type':'colorbutton','default':options['BGCOLOR'],'label':'Background Color'},
                'FONT':{'type':'font','default':options['FONT'],'label':'Font'},
                'FONTSIZE':{'type':'spinbox','default':options['FONTSIZE'],'range':(5,40),
                            'interval':1,'label':'Font Size'},
                'TIMEFORMAT':{'type':'combobox','default':options['TIMEFORMAT'],
                            'items':timeformats,'label':'Date/Time format'},
                'PRECISION':{'type':'spinbox','default':options['PRECISION'], 'range':(0,10),
                            'interval':1,'label':'Precision'},
                'SHOWPLOTTER': {'type':'checkbox','default':bool(options['SHOWPLOTTER']), 'label':'Show Plotter'},
                'PLOTSTYLE':{'type':'combobox','default':options['PLOTSTYLE'],
                            'items':plotstyles,'label':'Plot Style'},
                'DPI':{'type':'entry','default':options['DPI'],#'range':(20,300),'interval':10,
                        'label':'Plot DPI'},
                'ICONSIZE':{'type':'spinbox','default':options['ICONSIZE'],'range':(16,64), 'label':'Icon Size'},
                'THEME':{'type':'combobox','default':options['THEME'],'items': themes,
                        'label': 'Default Theme'}
                }
        sections = {'table':['ALIGNMENT','FONT','FONTSIZE',
                        'TIMEFORMAT','PRECISION','BGCOLOR'],
                    'view':['ICONSIZE','PLOTSTYLE','DPI','THEME','SHOWPLOTTER']
                    }

        dialog, self.widgets = dialogFromOptions(self, self.opts, sections)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(dialog)
        dialog.setFocus()
        bw = self.createButtons(self)
        self.layout.addWidget(bw)
        return

    def createButtons(self, parent):

        bw = self.button_widget = QWidget(parent)
        vbox = QHBoxLayout(bw)
        button = QPushButton("Apply")
        button.clicked.connect(self.apply)
        vbox.addWidget(button)
        button = QPushButton("Reset")
        button.clicked.connect(self.reset)
        vbox.addWidget(button)
        button = QPushButton("Close")
        button.clicked.connect(self.close)
        vbox.addWidget(button)
        return bw

    def apply(self):
        """Apply options to current table"""

        kwds = getWidgetValues(self.widgets)
        core.FONT = kwds['FONT']
        core.FONTSIZE = kwds['FONTSIZE']
        core.BGCOLOR = kwds['BGCOLOR']
        core.TIMEFORMAT = kwds['TIMEFORMAT']
        core.PRECISION = kwds['PRECISION']
        core.SHOWPLOTTER = kwds['SHOWPLOTTER']
        core.PLOTSTYLE = kwds['PLOTSTYLE']
        core.DPI = kwds['DPI']
        core.ICONSIZE = kwds['ICONSIZE']
        self.parent.theme = kwds['THEME']
        self.parent.refresh()
        self.parent.applySettings()
        return

    def updateWidgets(self, kwds=None):
        """Update widgets from stored or supplied kwds"""

        if kwds == None:
            kwds = self.kwds
        for k in kwds:
            setWidgetValues(self.widgets, {k: kwds[k]})
        return

    def setDefaults(self):
        """Populate default kwds dict"""

        self.kwds = {}
        for o in self.opts:
            self.kwds[o] = core.defaults[o]
        return

    def reset(self):
        """Reset to defaults"""

        self.setDefaults()
        self.updateWidgets()
        self.apply()
        return

class FindReplaceDialog(QWidget):
    """Qdialog for table query/filtering"""
    def __init__(self, parent, table, title=None, app=None):

        super(FindReplaceDialog, self).__init__(parent)
        self.parent = parent
        self.table = table
        self.app = app
        self.setWindowTitle(title)
        self.resize(400,200)
        self.case = True
        self.current = 0 #coords of found cells
        self.createWidgets()
        self.setMaximumHeight(180)
        return

    def createWidgets(self):
        """Create widgets"""

        df = self.table.model.df
        cols = list(df.columns)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.query_w = QLineEdit()
        self.layout.addWidget(QLabel('Query String'))
        self.layout.addWidget(self.query_w )
        self.query_w.returnPressed.connect(self.findAll)
        self.replace_w = QLineEdit()
        self.layout.addWidget(QLabel('Replace With'))
        self.layout.addWidget(self.replace_w )

        tb = self.createToolBar(self)
        self.layout.addWidget(tb)
        self.adjustSize()
        return

    def createToolBar(self, parent):

        items = {'Find All': {'action':self.findAll,'file':'findall'},
                 'Find Next': {'action':self.findNext,'file':'find'},
                 'Replace': {'action':self.replace,'file':'findreplace'},
                 'Case Sensitive': {'action':self.togglecase,'file':'lowercase','checkable':True}
                 }
        toolbar = QToolBar("Toolbar")
        toolbar.setOrientation(QtCore.Qt.Horizontal)
        addToolBarItems(toolbar, self, items)
        return toolbar

    def findAll(self):
        """Apply"""

        self.find()
        self.table.refresh()
        return

    def findNext(self):
        """Show next cell of search results"""

        table = self.table
        s = self.query_w.text()
        if len(self.coords)==0  or self.search_changed == True:
            self.find()
        if len(self.coords)==0:
            return
        idx = self.current
        i,j = self.coords[idx]
        index = table.model.index(i,j)
        #table.scrollTo(index, QAbstractItemView.EnsureVisible)
        table.selectRow(i)
        table.refresh()
        self.current+=1
        if self.current>=len(self.coords):
            self.current=0
        return

    def togglecase(self):

        sender = self.sender()
        self.case = sender.isChecked()
        return

    def find(self):
        """Do string search. Creates a masked dataframe for results and then stores each cell
        coordinate in a list."""

        table = self.table
        df = table.model.df
        df = df.astype('object').astype('str')
        s = self.query_w.text()
        self.search_changed = False
        self.clear()
        if s == '':
            return
        found = pd.DataFrame()
        for col in df:
            found[col] = df[col].str.contains(s, na=False, case=self.case)
        #set the masked dataframe so that highlighted cells are shown on redraw
        table.model.highlighted = found
        i=0
        self.coords = []
        for r,row in found.iterrows():
            j=0
            for col,val in row.iteritems():
                if val is True:
                    #print (r,col,val, i, j)
                    self.coords.append((i,j))
                j+=1
            i+=1
        self.current = 0
        #print (self.coords)
        return

    def replace(self):
        """Replace all instances of search text"""

        table = self.table
        table.storeCurrent()
        df = table.model.df
        s=self.query_w.text()
        r=self.replace_w.text()
        case = self.case
        table.model.df = df.replace(s,r,regex=True)
        table.refresh()
        self.search_changed = True
        return

    def clear(self):

        self.table.model.highlighted = None
        self.table.refresh()

    def onClose(self):

        self.clear()
        self.close()

class FilterDialog(QWidget):
    """Qdialog for table query/filtering"""
    def __init__(self, parent, table, title=None, app=None):

        super(FilterDialog, self).__init__(parent)
        self.parent = parent
        #self.app = self.parent.app
        self.table = table
        self.app = app
        self.setWindowTitle(title)
        self.resize(400,200)
        self.createWidgets()
        self.filters = []
        self.ignorecase = True
        #self.setMinimumHeight(200)
        #self.show()
        return

    def createToolBar(self, parent):

        items = {'Apply': {'action':self.apply,'file':'filter'},
                 'Add': {'action':self.addFilter,'file':'add'},
                 'Reset': {'action':self.refresh,'file':'table-refresh'},
                 'Copy to New Table': {'action':self.copyResult,'file':'subtable'},
                 'Subtract': {'action':self.removeFiltered,'file':'table-remove'},
                 'Ignore Case': {'action':self.togglecase,'file':'lowercase','checkable':True}
                 }
        toolbar = QToolBar("Toolbar")
        toolbar.setOrientation(QtCore.Qt.Horizontal)
        addToolBarItems(toolbar, self, items)
        return toolbar

    def createWidgets(self):
        """Create widgets"""

        df = self.table.model.df
        cols = list(df.columns)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.query_w = QLineEdit()
        self.layout.addWidget(QLabel('String filter'))
        self.layout.addWidget(self.query_w )
        self.query_w.returnPressed.connect(self.apply)
        w = self.column_w = QListWidget()
        w.setSelectionMode(QAbstractItemView.MultiSelection)
        #w.setFixedHeight(60)
        w.addItems(cols)
        self.layout.addWidget(QLabel('Display Columns'))
        self.layout.addWidget(self.column_w)
        tb = self.createToolBar(self)
        self.layout.addWidget(tb)
        self.adjustSize()
        return

    def refresh(self):
        """Reset the table"""

        table = self.table
        if table.filtered == True and hasattr(table, 'dataframe'):
            table.model.df = table.dataframe
            table.filtered = False
            table.refresh()
        return

    def update(self):
        """Update the column widgets if table has changed"""

        df = self.table.model.df
        cols = list(df.columns)
        self.column_w.clear()
        self.column_w.addItems(cols)
        return

    def togglecase(self):

        sender = self.sender()
        self.ignorecase = sender.isChecked()
        return

    def copyResult(self):

        table = self.table
        if table.filtered == False:
            return
        df = table.model.df
        self.app.addSheet(None, df)
        return

    def addFilter(self):
        """Add a filter using widgets"""

        df = self.table.model.df
        fb = FilterBar(self, self.table)
        self.layout.insertWidget(4,fb)
        self.filters.append(fb)
        return

    def apply(self):
        """Apply filters"""

        table = self.table
        if table.filtered == True and hasattr(table, 'dataframe'):
            table.model.df = table.dataframe
        df = table.model.df
        mask = None

        s = self.query_w.text()
        cols = [i.text() for i in self.column_w.selectedItems()]
        if len(cols)>0:
            df = df[cols]
        if s!='':
            try:
                mask = df.eval(s)
            except:
                mask = df.eval(s, engine='python')

        #add widget based filters
        if len(self.filters)>0:
            mask = self.applyWidgetFilters(df, mask)
        #apply mask
        if mask is not None:
            df = df[mask]
        self.filtdf = df
        table.dataframe = table.model.df.copy()
        table.filtered = True
        table.model.df = df
        table.model.layoutChanged.emit()
        table.refresh()
        return

    def applyWidgetFilters(self, df, mask=None):
        """Apply the widget based filters, returns a boolean mask"""

        if mask is None:
            mask = df.index==df.index

        for f in self.filters:
            col, val, op, b = f.getFilter()
            try:
                val = float(val)
            except:
                pass
            #print (col, val, op, b)
            print (self.ignorecase)
            if self.ignorecase == True:
                strval = "(?i)"+str(val).lower()
            else:
                strval = str(val)

            if op == 'contains':
                m = df[col].astype(str).str.contains(strval)
            elif op == 'equals':
                m = df[col]==val
            elif op == 'not equals':
                m = df[col]!=val
            elif op == '>':
                m = df[col]>val
            elif op == '<':
                m = df[col]<val
            elif op == 'is empty':
                m = df[col].isnull()
            elif op == 'not empty':
                m = ~df[col].isnull()
            elif op == 'excludes':
                m = -df[col].str.contains(strval)
            elif op == 'starts with':
                m = df[col].str.startswith(strval)
            elif op == 'ends with':
                m = df[col].str.endswith(strval)
            elif op == 'has length':
                m = df[col].str.len()>val
            elif op == 'is number':
                m = df[col].astype('object').str.isnumeric()
            elif op == 'is lowercase':
                m = df[col].astype('object').str.islower()
            elif op == 'is uppercase':
                m = df[col].astype('object').str.isupper()
            else:
                continue
            if b == 'AND':
                mask = mask & m
            elif b == 'OR':
                mask = mask | m
            elif b == 'NOT':
                mask = mask ^ m
        return mask

    def removeFiltered(self):
        """Subtract current filtered result from original table"""

        reply = QMessageBox.question(self, 'Perform Action?',
                             'This will overwrite the current table. Are you sure?',
                              QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        table = self.table
        if table.filtered == False:
            return
        idx = list(self.filtdf.index)
        df = table.dataframe
        table.dataframe = None
        table.filtered = False
        table.model.df = df.loc[~df.index.isin(idx)]
        table.model.layoutChanged.emit()
        table.refresh()
        return

    def onClose(self):

        self.table.showAll()
        self.close()

class FilterBar(QWidget):
    """Single Widget based filter"""
    def __init__(self, parent, table):
        super(FilterBar, self).__init__(parent)
        self.parent = parent
        #self.app = self.parent.app
        self.table = table
        self.createWidgets()

    def createWidgets(self):
        """Create widgets"""

        operators = ['contains','excludes','equals','not equals','>','<','is empty','not empty',
                     'starts with','ends with','has length','is number','is lowercase','is uppercase']
        booleanops = ['AND','OR','NOT']
        df = self.table.model.df
        cols = list(df.columns)
        l = self.layout = QHBoxLayout(self)
        self.setLayout(self.layout)
        w = self.boolean_w = QComboBox()
        w.addItems(booleanops)
        l.addWidget(self.boolean_w)
        w = self.column_w = QComboBox()
        w.addItems(cols)
        #l.addWidget(QLabel('Column:'))
        l.addWidget(self.column_w)
        w = self.operator_w = QComboBox()
        w.addItems(operators)
        l.addWidget(self.operator_w)

        self.term_w = QLineEdit()
        self.term_w.returnPressed.connect(self.parent.apply)
        l.addWidget(self.term_w )
        icon = QIcon(os.path.join(iconpath,'remove.png'))
        btn = QPushButton()
        btn.setIcon(icon)
        btn.setMaximumWidth(30)
        btn.clicked.connect(self.onClose)
        l.addWidget(btn)
        return

    def getFilter(self):
        """Get filter values for this instance"""

        col = self.column_w.currentText()
        val = self.term_w.text()
        op = self.operator_w.currentText()
        booleanop = self.boolean_w.currentText()
        return col, val, op, booleanop

    def onClose(self, ce):
        self.parent.filters.remove(self)
        self.close()

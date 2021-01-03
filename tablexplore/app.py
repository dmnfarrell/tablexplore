#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
    TablExplore app
    Created November 2020
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
import sys,os,platform,time
import pickle, gzip
from collections import OrderedDict
from PySide2 import QtCore
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import QObject, Signal, Slot
import pandas as pd
from .core import DataFrameModel, DataFrameTable, DataFrameWidget
from .plotting import PlotViewer
from . import util, data, core, dialogs

homepath = os.path.expanduser("~")
module_path = os.path.dirname(os.path.abspath(__file__))
stylepath = os.path.join(module_path, 'styles')
iconpath = os.path.join(module_path, 'icons')

class Application(QMainWindow):
    def __init__(self, project_file=None, csv_file=None):

        QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Tablexplore")
        self.setWindowIcon(QIcon(os.path.join(module_path,'logo.png')))

        self.createMenu()
        self.main = QTabWidget(self)
        self.main.setTabsClosable(True)
        self.main.tabCloseRequested.connect(lambda index: self.removeSheet(index))
        screen_resolution = QGuiApplication.primaryScreen().availableGeometry()
        width, height = screen_resolution.width()*0.7, screen_resolution.height()*.7
        self.setGeometry(QtCore.QRect(200, 200, width, height))
        self.setMinimumSize(400,300)

        self.main.setFocus()
        self.setCentralWidget(self.main)
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.createToolBar()

        self.proj_label = QLabel("")
        self.statusbar.addWidget(self.proj_label, 1)
        self.proj_label.setStyleSheet('color: blue')
        self.style = 'default'
        self.font = 'monospace'
        self.recent_files = ['']
        self.recent_urls = []
        self.plots = {}

        self.loadSettings()
        self.showRecentFiles()
        if project_file != None:
            self.openProject(project_file)
        elif csv_file != None:
            self.importFile(csv_file)
        else:
            self.newProject()
        self.threadpool = QtCore.QThreadPool()
        return

    def loadSettings(self):
        """Load GUI settings"""

        s = self.settings = QtCore.QSettings('tablexplore','default')
        try:
            self.resize(s.value('window_size'))
            self.move(s.value('window_position'))
            self.setStyle(s.value('style'))
            core.FONT = s.value("font")
            core.FONTSIZE = int(s.value("fontsize"))
            r = s.value("recent_files")
            if r != '':
                self.recent_files = r.split(',')
            r = s.value("recent_urls")
            if r != '':
                self.recent_urls = r.split('^^')
        except:
            pass

        return

    def saveSettings(self):
        """Save GUI settings"""

        self.settings.setValue('window_size', self.size())
        self.settings.setValue('window_position', self.pos())
        self.settings.setValue('style', self.style)
        self.settings.setValue('font', core.FONT)
        self.settings.setValue('fontsize', core.FONTSIZE)
        self.settings.setValue('recent_files',','.join(self.recent_files))
        self.settings.setValue('recent_urls','^^'.join(self.recent_urls))
        if hasattr(self, 'plotgallery'):
            self.settings.setValue('plotgallery_size',self.plotgallery.size())
        self.settings.sync()
        return

    def setStyle(self, style='default'):
        """Change interface style."""

        if style == 'default':
            	self.setStyleSheet("")
        else:
            f = open(os.path.join(stylepath,'%s.qss' %style), 'r')
            self.style_data = f.read()
            f.close()
            self.setStyleSheet(self.style_data)
        self.style = style
        return

    def createToolBar(self):

        items = {'new': {'action': lambda: self.newProject(ask=True),'file':'document-new'},
                 'open': {'action':self.openProject,'file':'document-open'},
                 'save': {'action': lambda: self.saveProject(None),'file':'save'},
                 'zoom out': {'action':self.zoomOut,'file':'zoom-out'},
                 'zoom in': {'action':self.zoomIn,'file':'zoom-in'},
                 'decrease columns': {'action': lambda: self.changeColumnWidths(.9),'file':'decrease-width'},
                 'increase columns': {'action': lambda: self.changeColumnWidths(1.1),'file':'increase-width'},
                 'add sheet': {'action':self.addSheet,'file':'add'},
                 #'lock': {'action':self.lockTable,'file':'lock'},
                 'clean data': {'action':lambda: self._call('cleanData'),'file':'clean'},
                 'table to text': {'action':lambda: self._call('showAsText'),'file':'tabletotext'},
                 'table info': {'action':lambda: self._call('info'),'file':'tableinfo'},
                 'plot gallery': {'action': self.showPlotGallery,'file':'plot-gallery'},
                 'preferences': {'action':self.preferences,'file':'preferences-system'},
                 'quit': {'action':self.fileQuit,'file':'application-exit'}
                }

        toolbar = QToolBar("My main toolbar")
        self.addToolBar(toolbar)
        for i in items:
            if 'file' in items[i]:
                iconfile = os.path.join(iconpath,items[i]['file']+'.png')
                icon = QIcon(iconfile)
            else:
                icon = QIcon.fromTheme(items[i]['icon'])
            btn = QAction(icon, i, self)
            btn.triggered.connect(items[i]['action'])
            #btn.setCheckable(True)
            toolbar.addAction(btn)

        return

    def createMenu(self):

        self.file_menu = QMenu('&File', self)
        self.file_menu.addAction('&New', lambda: self.newProject(ask=True),
                QtCore.Qt.CTRL + QtCore.Qt.Key_N)
        self.file_menu.addAction('&Open', self.openProject,
                QtCore.Qt.CTRL + QtCore.Qt.Key_O)
        self.recent_files_menu = QMenu("Recent Projects",
            self.file_menu)
        self.file_menu.addAction(self.recent_files_menu.menuAction())
        self.file_menu.addAction('&Save', self.saveProject,
                QtCore.Qt.CTRL + QtCore.Qt.Key_S)
        self.file_menu.addAction('&Save As', self.saveAsProject)
        self.file_menu.addAction('&Import File', self.importFile)
        self.file_menu.addAction('&Import HDF5', self.importHDF)
        self.file_menu.addAction('&Import URL', self.importURL)
        self.file_menu.addAction('&Export As', self.exportAs)
        self.file_menu.addAction('&Quit', self.fileQuit,
                QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.edit_menu = QMenu('&Edit', self)
        self.menuBar().addMenu(self.edit_menu)
        self.undo_item = self.edit_menu.addAction('&Undo', self.undo,
                QtCore.Qt.CTRL + QtCore.Qt.Key_Z)
        #self.undo_item.setDisabled(True)
        self.edit_menu.addAction('&Preferences', self.preferences)

        self.view_menu = QMenu('&View', self)
        self.menuBar().addMenu(self.view_menu)
        self.view_menu.addAction('&Zoom In', self.zoomIn,
                QtCore.Qt.CTRL + QtCore.Qt.Key_Equal)
        self.view_menu.addAction('&Zoom Out', self.zoomOut,
                QtCore.Qt.CTRL + QtCore.Qt.Key_Minus)
        self.view_menu.addAction('&Decrease Column Width', lambda: self.changeColumnWidths(.9))
        self.view_menu.addAction('&Increase Column Width', self.changeColumnWidths)
        self.style_menu = QMenu("Styles",  self.view_menu)
        self.style_menu.addAction('&Default', self.setStyle)
        self.style_menu.addAction('&Light', lambda: self.setStyle('light'))
        self.style_menu.addAction('&Dark', lambda: self.setStyle('dark'))
        self.view_menu.addAction(self.style_menu.menuAction())

        self.sheet_menu = QMenu('&Sheet', self)
        self.menuBar().addMenu(self.sheet_menu)
        self.sheet_menu.addAction('&Add', self.addSheet)
        self.sheet_menu.addAction('&Rename', self.renameSheet)
        self.sheet_menu.addAction('&Copy', self.copySheet)

        self.tools_menu = QMenu('&Tools', self)
        self.tools_menu.addAction('&Table Info', lambda: self._call('info'),
                QtCore.Qt.CTRL + QtCore.Qt.Key_I)
        self.tools_menu.addAction('&Clean Data', lambda: self._call('cleanData'))
        self.tools_menu.addAction('&Find Duplicates', lambda: self._call('findDuplicates'))
        self.tools_menu.addAction('&Convert Numeric', lambda: self._call('convertNumeric'))
        self.tools_menu.addAction('&Convert Column Names', lambda: self._call('convertColumnNames'))
        self.tools_menu.addAction('&Time Series Resample', lambda: self._call('resample'))
        self.tools_menu.addAction('&Table to Text', lambda: self._call('showAsText'),
                QtCore.Qt.CTRL + QtCore.Qt.Key_T)
        self.tools_menu.addAction('&Python Interpreter', self.interpreter)
        self.menuBar().addMenu(self.tools_menu)

        self.dataset_menu = QMenu('&Datasets', self)
        self.menuBar().addMenu(self.dataset_menu)
        self.dataset_menu.addAction('&Sample', lambda: self.getSampleData('sample'))
        self.dataset_menu.addAction('&Iris', lambda: self.getSampleData('iris'))
        self.dataset_menu.addAction('&Titanic', lambda: self.getSampleData('titanic'))
        self.dataset_menu.addAction('&Pima Diabetes', lambda: self.getSampleData('pima'))

        self.plots_menu = QMenu('&Plots', self)
        self.menuBar().addMenu(self.plots_menu)
        self.plots_menu.addAction('&Store Plot', lambda: self.storePlot())
        self.plots_menu.addAction('&Show Plots', lambda: self.showPlotGallery())

        self.help_menu = QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)
        self.help_menu.addAction('&About', self.about)

        #plot shortcut
        self.plotshc = QShortcut(QKeySequence('Ctrl+P'), self)
        self.plotshc.activated.connect(self.replot)
        return

    def _call(self, func, **args):
        """Call a table function from it's string name"""

        table = self.getCurrentTable()
        getattr(table, func)(**args)
        return

    def _check_snap(self):

        if os.environ.has_key('SNAP_USER_COMMON'):
            print ('running inside snap')
            return True
        return False

    def _checkTables(self):
        """Check tables before saving that so we are not saving
        filtered copies"""

        for s in self.sheets:
            t=self.sheets[s]
            if t.filtered==True:
                t.showAll()
        return

    @Slot(str)
    def stateChanged(self, bool):
        print(bool)

    def showRecentFiles(self):
        """Populate recent files menu"""

        from functools import partial
        if self.recent_files == None:
            return
        for fname in self.recent_files:
            self.recent_files_menu.addAction(fname, partial(self.openProject, fname))
        self.recent_files_menu.setEnabled(len(self.recent_files))
        return

    def addRecentFile(self, fname):
        """Add file to recent if not present"""

        if fname and fname not in self.recent_files:
            self.recent_files.insert(0, fname)
            if len(self.recent_files) > 5:
                self.recent_files.pop()
        self.recent_files_menu.setEnabled(len(self.recent_files))
        return

    def newProject(self, data=None, ask=False):
        """New project"""

        if ask == True:
            reply = QMessageBox.question(self, 'Are you sure?',
                                 'Save current project?',
                                 QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.saveProject()
        if not type(data) is dict:
            data = None
        self.main.clear()
        self.sheets = OrderedDict()
        self.filename = None
        self.projopen = True
        self.plots = {}
        if data != None:
            for s in data.keys():
                if s in ['meta','plots']:
                    continue
                df = data[s]['table']
                if 'meta' in data[s]:
                    meta = data[s]['meta']
                else:
                    meta=None
                self.addSheet(s, df, meta)
            if 'plots' in data:
                self.plots = data['plots']
        else:
            self.addSheet('dataset1')
        return

    def closeProject(self):
        """Close"""

        return

    def openProject(self, filename=None, asksave=False):
        """Open project file"""

        w=True
        if asksave == True:
            w = self.closeProject()
        if w == None:
            return

        if filename == None:
            options = QFileDialog.Options()
            filename, _ = QFileDialog.getOpenFileName(self,"Open Project",
                                  "","tablexplore Files (*.txpl);;All files (*.*)",
                                  options=options)

        if not filename:
            return
        if not os.path.exists(filename):
            print ('no such file')
            self.removeRecent(filename)
            return
        ext = os.path.splitext(filename)[1]
        if ext != '.txpl':
            print ('does not appear to be a project file')
            return
        if os.path.isfile(filename):
            data = pickle.load(gzip.GzipFile(filename, 'r'))
        else:
            print ('no such file')
            self.quit()
            return
        self.newProject(data)
        self.filename = filename

        self.proj_label.setText(self.filename)
        self.projopen = True
        self.defaultsavedir = os.path.dirname(os.path.abspath(filename))
        self.addRecentFile(filename)
        return

    def saveAsProject(self):
        """Save as a new project filename"""

        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(self,"Save Project",
                                                  "","tablexplore Files (*.txpl);;All files (*.*)",
                                                  options=options)
        if not filename:
            return

        self.filename = filename
        self.do_saveProject(filename)
        self.addRecentFile(filename)
        return

    def saveProject(self, filename=None):
        """Save project"""

        if self.filename != None:
            filename = self.filename
        if filename is None:
            self.saveAsProject()
        if not filename:
            return
        self.filename = filename
        if not os.path.splitext(filename)[1] == '.txpl':
            self.filename += '.txpl'
        self.defaultsavedir = os.path.dirname(os.path.abspath(filename))
        self.do_saveProject(self.filename)
        #self.saveWithProgress(self.filename)
        return

    def saveWithProgress(self, filename):
        """Save with progress bar"""

        class ProgressWidget(QDialog):

            def __init__(self, parent=None):
                super(ProgressWidget, self).__init__(parent)
                layout = QVBoxLayout(self)
                self.setWindowTitle('Saving..')
                self.setGeometry(500, 400, 400, 200)

                #self.setGeometry(QtCore.QRect(200, 200, width, height))

                self.setGeometry(
                        QStyle.alignedRect(
                            QtCore.Qt.LeftToRight,
                            QtCore.Qt.AlignCenter,
                            self.size(),
                            QGuiApplication.primaryScreen().availableGeometry(),
                        ))
                # Create a progress bar
                self.progressbar = QProgressBar(self)
                self.progressbar.setRange(0,0)
                layout.addWidget(self.progressbar)
                self.progressbar.setGeometry(30, 40, 400, 200)
                #button = QPushButton("Start", self)
                #layout.addWidget(button)
                #button.clicked.connect(self.onStart)

            def start(self):
                self.progressbar.setRange(0,0)

            def onFinished(self):
                print ('stop')
                self.progressbar.setRange(0,1)
                self.close()

        class SaveThread(QtCore.QThread):
            taskFinished = Signal()
            def run(self):
                print('run')
                time.sleep(3)
                #self.do_saveProject(self.filename)
                #func()
                self.taskFinished.emit()

        dlg = ProgressWidget()
        dlg.exec_()
        func = lambda: time.sleep(5)
        self.savetask = SaveThread()
        self.savetask.taskFinished.connect(dlg.onFinished)
        self.savetask.start()
        return

    def do_saveProject(self, filename):
        """Does the actual saving. Save sheets inculding table dataframes
           and meta data as dict to compressed pickle.
        """

        data={}
        for i in self.sheets:
            #print (i)
            tablewidget = self.sheets[i]
            table = tablewidget.table
            data[i] = {}
            #save dataframw with current column order
            df = table.model.df
            cols = table.getColumnOrder()
            data[i]['table'] = df[cols]
            data[i]['meta'] = self.saveMeta(tablewidget)
        data['plots'] = self.plots
        file = gzip.GzipFile(filename, 'w')
        pickle.dump(data, file)
        return

    def saveMeta(self, tablewidget):
        """Save meta data such as current plot options and certain table attributes.
         These are re-loaded when the sheet is opened."""

        meta = {}
        pf = tablewidget.pf
        pf.applyPlotoptions()
        table = tablewidget.table
        #save plot options
        meta['generalopts'] = pf.generalopts.kwds
        #meta['mplopts3d'] = pf.mplopts3d.kwds
        meta['labelopts'] = pf.labelopts.kwds
        meta['axesopts'] = pf.axesopts.kwds

        #save table selections
        meta['table'] = util.getAttributes(table)
        meta['table']['column_widths'] = table.getColumnWidths()
        meta['plotviewer'] = util.getAttributes(pf)
        #print (meta['plotviewer'])
        #save child table if present
        if tablewidget.subtable != None:
            meta['subtable'] = tablewidget.subtable.table.model.df
        #    meta['childselected'] = util.getAttributes(table.child)

        return meta

    def loadMeta(self, table, meta):
        """Load meta data for a sheet/table, this includes plot options and
        table selections"""

        tablesettings = meta['table']
        if 'subtable' in meta:
            subtable = meta['subtable']
            #childsettings = meta['childselected']
        else:
            subtable = None
        #load plot options
        opts = {'generalopts': table.pf.generalopts,
                #'mplopts3d': table.pf.mplopts3d,
                'labelopts': table.pf.labelopts,
                'axesopts': table.pf.axesopts,
                }
        for m in opts:
            if m in meta and meta[m] is not None:
                #util.setAttributes(opts[m], meta[m])
                #print (m,meta[m])
                opts[m].updateWidgets(meta[m])
                #check options loaded for missing values
                #avoids breaking file saves when options changed
                #defaults = plotting.get_defaults(m)
                #for key in defaults:
                #    if key not in opts[m].opts:
                #        opts[m].opts[key] = defaults[key]

        #load table settings
        util.setAttributes(table.table, tablesettings)
        if 'column_widths' in tablesettings:
            table.table.setColumnWidths(tablesettings['column_widths'])
        table.refresh()
        #load plotviewer
        if 'plotviewer' in meta:
            #print (meta['plotviewer'])
            fig = meta['plotviewer']['fig']
            table.pf.setFigure(fig)
            table.pf.canvas.draw()
            #util.setAttributes(table.pf, meta['plotviewer'])
            #table.pf.updateWidgets()

        if subtable is not None:
            table.showSubTable(df=subtable)
            #util.setAttributes(table.child, childsettings)

        #redraw col selections
        #if type(table.multiplecollist) is tuple:
        #    table.multiplecollist = list(table.multiplecollist)
        #table.drawMultipleCols()
        return

    def importFile(self, filename=None):

        self.addSheet()
        w = self.getCurrentTable()
        w.importFile(filename)
        return

    def importHDF(self):

        self.addSheet()
        w = self.getCurrentTable()
        w.importHDF()
        return

    def importURL(self):
        """Import from URL"""

        self.addSheet()
        w = self.getCurrentTable()
        recent = self.recent_urls
        url = w.importURL(recent)
        if url != False and url not in self.recent_urls:
            self.recent_urls.append(url)
        return

    def exportAs(self):
        """Export as"""

        options = QFileDialog.Options()
        w = self.getCurrentTable()
        filename, _ = QFileDialog.getSaveFileName(self,"Export",
                             "","csv files (*.csv);;xlsx files (*.xlsx);;xls Files (*.xls);;hdf files (*.hdf5);;All Files (*)",
                             options=options)
        df = w.table.model.df
        ext = os.path.splitext(filename)[1]
        if ext == '.csv':
            df.to_csv(filename)
        elif ext == '.hdf5':
            df.to_hdf(filename)
        elif ext == '.xls':
            df.to_excel(filename)
        return

    def addSheet(self, name=None, df=None, meta=None):
        """Add a new sheet"""

        names = self.sheets.keys()
        if name is None or name in self.sheets:
            name = 'dataset'+str(len(self.sheets)+1)

        sheet = QSplitter(self.main)
        idx = self.main.addTab(sheet, name)
        #provide reference to self to dataframewidget
        dfw = DataFrameWidget(sheet, dataframe=df, app=self,
                                font=core.FONT, fontsize=core.FONTSIZE)
        sheet.addWidget(dfw)

        self.sheets[name] = dfw
        self.currenttable = dfw
        pf = dfw.createPlotViewer(sheet)
        sheet.addWidget(pf)
        sheet.setSizes((500,1000))
        #reload attributes of table and plotter if present
        if meta != None:
            self.loadMeta(dfw, meta)
        self.main.setCurrentIndex(idx)
        return

    def removeSheet(self, index, ask=True):
        """Remove sheet"""

        if ask == True:
            reply = QMessageBox.question(self, 'Delete this sheet?',
                                 'Are you sure?', QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.No:
                return False
        name = self.main.tabText(index)
        del self.sheets[name]
        self.main.removeTab(index)
        return

    def renameSheet(self):
        """Rename the current sheet"""

        index = self.main.currentIndex()
        name = self.main.tabText(index)
        new, ok = QInputDialog.getText(self, 'New name', 'Name:',
                    QLineEdit.Normal, name)
        if ok:
            self.sheets[new] = self.sheets[name]
            del self.sheets[name]
            self.main.setTabText(index, new)
        return

    def copySheet(self):
        """Copy sheet"""

        index = self.main.currentIndex()
        name = self.main.tabText(index)
        df = self.sheets[name].table.model.df
        new, ok = QInputDialog.getText(self, 'New name', 'Name:',
                    QLineEdit.Normal, name+'_copy')
        if ok:
            self.addSheet(new, df)
        return

    def load_dataframe(self, df, name=None, select=False):
        """Load a DataFrame into a new sheet
           Args:
            df: dataframe
            name: name of new sheet
            select: set new sheet as selected
        """

        if hasattr(self,'sheets'):
            self.addSheet(sheetname=name, df=df, select=select)
        else:
            data = {name:{'table':df}}
            self.newProject(data)
        return

    def load_pickle(self, filename):
        """Load a pickle file"""

        df = pd.read_pickle(filename)
        name = os.path.splitext(os.path.basename(filename))[0]
        self.load_dataframe(df, name)
        return

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        """Close event"""

        reply = QMessageBox.question(self, 'Close',
                                 'Save current project?',
                                  QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        if reply == QMessageBox.Cancel:
            return
        if reply == QMessageBox.Yes:
            self.saveProject()
        for s in self.sheets:
            self.sheets[s].close()
        self.saveSettings()
        if hasattr(self,'plotgallery'):
            self.plotgallery.close()
        self.fileQuit()
        return

    def getSampleData(self, name, rows=None):
        """Sample table"""

        ok = True
        sheetname = name
        if name in self.sheets:
            i = len(self.sheets)
            sheetname = name + '-' + str(i)
        if name == 'sample':
            if rows is None:
                opts = {'rows':{'type':'spinbox','default':10,'range':(1,1e7)},
                        'cols':{'type':'spinbox','default':5,'range':(1,26)}}
                dlg = dialogs.MultipleInputDialog(self, opts, title='Sample data',
                                    width=250,height=150)
                dlg.exec_()
                if not dlg.accepted:
                    return
                kwds = dlg.values
                rows = kwds['rows']
                cols = kwds['cols']
            if ok:
                df = data.getSampleData(rows,cols)
            else:
                return
        else:
            df = data.getPresetData(name)
        self.addSheet(sheetname,df)
        return

    def getCurrentTable(self):
        """Return the currently used table"""

        idx = self.main.currentIndex()
        name= self.main.tabText(idx)
        table = self.sheets[name]
        return table

    def replot(self):
        """Plot current"""

        w = self.getCurrentTable()
        pf = w.pf
        pf.replot()

    def zoomIn(self):

        w = self.getCurrentTable()
        w.table.zoomIn()
        return

    def zoomOut(self):

        w = self.getCurrentTable()
        w.table.zoomOut()
        return

    def changeColumnWidths(self, factor=1.1):
        w = self.getCurrentTable()
        w.table.changeColumnWidths(factor)

    def undo(self):

        w = self.getCurrentTable()
        w.table.undo()
        w.refresh()
        return

    def refresh(self):
        """Refresh all tables"""

        for s in self.sheets:
            w = self.sheets[s].table
            w.font = core.FONT
            w.fontsize = core.FONTSIZE
            w.refresh()
        return

    def storePlot(self):
        """Cache the current plot so it can be viewed later"""

        w = self.getCurrentTable()
        index = self.main.currentIndex()
        name = self.main.tabText(index)
        #get the current figure and make a copy of it by using pickle
        fig = w.pf.fig
        p = pickle.dumps(fig)
        fig = pickle.loads(p)
        t = time.strftime("%H:%M:%S")
        label = name+'-'+t
        self.plots[label] = fig
        if hasattr(self, 'plotgallery'):
            self.plotgallery.update(self.plots)
        return

    def showPlotGallery(self):
        """Show stored plot figures"""

        from . import plotting
        if not hasattr(self, 'plotgallery'):
            self.plotgallery = plotting.PlotGallery()
            try:
                self.plotgallery.resize(self.settings.value('plotgallery_size'))
            except:
                pass
        self.plotgallery.update(self.plots)
        self.plotgallery.show()
        self.plotgallery.activateWindow()
        return

    def interpreter(self):
        """Launch python interpreter"""

        table = self.getCurrentTable()
        table.showInterpreter()
        return

    def preferences(self):
        """Preferences dialog"""

        from . import dialogs
        opts = {'font':core.FONT, 'fontsize':core.FONTSIZE}
        dlg = dialogs.PreferencesDialog(self, opts)
        dlg.exec_()
        return

    def online_documentation(self,event=None):
        """Open the online documentation"""

        import webbrowser
        link='https://github.com/dmnfarrell/tablexplore'
        webbrowser.open(link,autoraise=1)
        return

    def about(self):
        from . import __version__
        import matplotlib
        import PySide2
        pandasver = pd.__version__
        pythonver = platform.python_version()
        mplver = matplotlib.__version__
        qtver = PySide2.QtCore.__version__

        text='Tablexplore Application\n'\
                +'Version '+__version__+'\n'\
                +'Copyright (C) Damien Farrell 2018-\n'\
                +'This program is free software; you can redistribute it and/or\n'\
                +'modify it under the terms of the GNU General Public License '\
                +'as published by the Free Software Foundation; either version 3 '\
                +'of the License, or (at your option) any later version.\n'\
                +'Using Python v%s, PySide2 v%s\n' %(pythonver, qtver)\
                +'pandas v%s, matplotlib v%s' %(pandasver,mplver)

        msg = QMessageBox.about(self, "About", text)
        return

def main():
    import sys, os

    from argparse import ArgumentParser
    parser = ArgumentParser()
    #parser.add_argument("-f", "--file", dest="msgpack",
    #                    help="Open a dataframe as msgpack", metavar="FILE")
    parser.add_argument("-p", "--project", dest="project_file",
                        help="Open a dataexplore project file", metavar="FILE")
    parser.add_argument("-i", "--csv", dest="csv_file",
                        help="Import a csv file", metavar="FILE")
    #parser.add_argument("-x", "--excel", dest="excel",
    #                    help="Import an excel file", metavar="FILE")
    #parser.add_argument("-t", "--test", dest="test",  action="store_true",
    #                    default=False, help="Run a basic test app")
    args = vars(parser.parse_args())

    app = QApplication(sys.argv)
    aw = Application(**args)
    aw.show()
    app.exec_()

if __name__ == '__main__':
    main()

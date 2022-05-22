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
import sys,os,platform,time,traceback
import pickle, gzip
from collections import OrderedDict
from .qt import *
import pandas as pd
from .core import DataFrameModel, DataFrameTable, DataFrameWidget
from .plotting import PlotViewer
from . import util, core, dialogs, widgets, plotting

homepath = os.path.expanduser("~")
module_path = os.path.dirname(os.path.abspath(__file__))
stylepath = os.path.join(module_path, 'styles')
iconpath = os.path.join(module_path, 'icons')
pluginiconpath = os.path.join(module_path, 'plugins', 'icons')

splittercss = """QSplitter::handle:hover {
border: 0.1ex dashed #777;
width: 15px;
margin-top: 10px;
margin-bottom: 10px;
border-radius: 4px;
}
"""

dockstyle = '''
    QDockWidget {
        max-width:240px;
    }
    QDockWidget::title {
        background-color: lightblue;
    }
    QScrollBar:vertical {
         width: 15px;
         margin: 1px 0 1px 0;
     }
    QScrollBar::handle:vertical {
         min-height: 20px;
     }
'''

class Application(QMainWindow):
    def __init__(self, project_file=None, csv_file=None, excel_file=None):

        QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Tablexplore")
        self.setWindowIcon(QIcon(os.path.join(module_path,'logo.svg')))
        self.createMenu()
        #self.main = QMdiArea(self)
        self.main = QWidget(self)
        self.tabs = QTabWidget(self.main)
        layout = QHBoxLayout(self.main)
        layout.addWidget(self.tabs)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(lambda index: self.removeSheet(index))
        self.tabs.currentChanged.connect(lambda index: self.tabSelected(index))
        screen_resolution = QGuiApplication.primaryScreen().availableGeometry()
        width, height = int(screen_resolution.width()*0.7), int(screen_resolution.height()*.7)
        if screen_resolution.width()>1024:
            self.setGeometry(QtCore.QRect(200, 200, width, height))
        self.setMinimumSize(400,300)

        self.main.setFocus()
        self.setCentralWidget(self.main)

        #plot docks
        plotting.update_colormaps()
        self.addDockWidgets()
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.createToolBar()

        self.proj_label = QLabel("")
        self.statusbar.addWidget(self.proj_label, 1)
        self.proj_label.setStyleSheet('color: blue')
        self.theme = 'Fusion'
        self.font = 'monospace'
        self.recent_files = ['']
        self.recent_urls = []
        self.scratch_items = {}
        self.openplugins = {}

        self.loadSettings()
        self.setTheme()
        self.setIconSize(QtCore.QSize(core.ICONSIZE, core.ICONSIZE))
        self.showRecentFiles()
        self.startLogging()

        if project_file != None:
            self.openProject(project_file)
        elif csv_file != None:
            self.newProject()
            self.importFile(csv_file)
        elif excel_file != None:
            self.newProject()
            self.importExcel(excel_file)
        else:
            self.newProject()
        self.threadpool = QtCore.QThreadPool()
        self.discoverPlugins()
        return

    def addDockWidgets(self):
        """Add plot dialogs to dock"""

        style = '''
            QWidget {
                font-size: 12px;
                max-width: 220px;
            }
            QLabel {
                min-width: 60px;
                width:80px;
            }
            QPlainTextEdit {
                max-height: 100px;
                min-width: 100px;
            }
            QScrollBar:vertical {
                 width: 15px;
             }
            QComboBox {
                combobox-popup: 0;
                max-height: 30px;
                max-width: 100px;
            }
            QListView::item:selected {
                min-width: 300px;}
        '''

        opts = plotting.defaultOptions()
        self.plotwidgets = {}
        docks = {}
        for name in opts:
            dock = QDockWidget(name)
            dock.setStyleSheet(dockstyle)
            area = QScrollArea()
            area.setWidgetResizable(True)
            dock.setWidget(area)
            dialog, widgets = opts[name].showDialog(area, wrap=2, section_wrap=1,
                                style=style)
            area.setWidget(dialog)
            self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
            self.plotwidgets[name] = widgets
            docks[name] = dock

        self.tabifyDockWidget(docks['labels'], docks['axes'])
        docks['labels'].raise_()
        self.docks = docks

        #add dock menu items
        for name in ['general','format','labels','axes']:
            action = self.docks[name].toggleViewAction()
            self.dock_menu.addAction(action)
            action.setCheckable(True)
        #series dock
        #self.addSeriesDock()
        return

    '''def addSeriesDock(self):
        """Add series dock. Updated by plotter when selections changed."""

        dock = QDockWidget('series')
        dock.setStyleSheet("QDockWidget::title {background-color: #99ccff;}")
        area = QScrollArea()
        area.setWidgetResizable(True)
        dock.setWidget(area)
        self.seriesarea = area
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        return'''

    def replot(self):
        """Plot current"""

        w = self.getCurrentTable()
        pf = w.pf
        pf.replot()
        return

    def tabSelected(self, index):
        """Re-load plot widgets for current tab"""

        name = self.tabs.tabText(index)
        if not name in self.sheets:
            return
        table = self.sheets[name]
        #print (table.pf)
        #get plot options and update widgets
        self.updatePlotWidgets(table)
        #update any plugins to use the current table if needed
        self.updatePlugins()
        return

    def updatePlotWidgets(self, table):
        """Update plot widgets from values in table"""

        for key in self.plotwidgets:
            opts = table.pf.opts[key]
            opts.widgets = self.plotwidgets[key]
            opts.updateWidgets()
        table.pf.updateData()
        return

    def updatePlugins(self):
        """Update table for a plugin if it needs it"""

        for o in self.openplugins:
            print (o)
            w = self.getCurrentTable()
            self.openplugins[o].table = w
        return

    def startLogging(self):
        """Logging"""

        import logging
        if platform.system() == 'Windows':
            path = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.ConfigLocation)
            if not os.path.exists(path):
                os.makedirs(path)
        else:
            path = os.path.dirname(self.settings.fileName())
        self.logfile = os.path.join(path, 'error.log')
        logging.basicConfig(filename=self.logfile,format='%(asctime)s %(message)s')
        return

    def checkSettings(self):
        """Check for missing settings"""

        for s in core.defaults:
            k = s.lower()
            if k not in self.settings.childKeys():
                self.settings.setValue(k,core.defaults[s])

    def loadSettings(self):
        """Load GUI settings"""

        s = self.settings = QtCore.QSettings('tablexplore','default')
        self.checkSettings()
        try:
            self.resize(s.value('window_size'))
            self.move(s.value('window_position'))
            self.theme = s.value('theme')
            core.FONT = s.value("font")
            core.FONTSIZE = int(s.value("fontsize"))
            core.BGCOLOR = s.value('bgcolor')
            core.COLUMNWIDTH = int(s.value("columnwidth"))
            core.TIMEFORMAT = s.value("timeformat")
            core.PRECISION = int(s.value("precision"))
            core.SHOWPLOTTER = util.valueToBool(s.value("showplotter"))
            core.PLOTSTYLE = s.value("plotstyle")
            core.DPI = int(s.value("dpi"))
            import matplotlib as mpl
            mpl.rcParams['savefig.dpi'] = core.DPI
            core.ICONSIZE = int(s.value("iconsize"))
            r = s.value("recent_files")
            if r != '':
                rct = r.split(',')
                self.recent_files = [f for f in rct if os.path.exists(f)]
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
        self.settings.setValue('theme', self.theme)
        self.settings.setValue('columnwidth', core.COLUMNWIDTH)
        self.settings.setValue('iconsize', core.ICONSIZE)
        self.settings.setValue('font', core.FONT)
        self.settings.setValue('fontsize', core.FONTSIZE)
        self.settings.setValue('bgcolor', core.BGCOLOR)
        self.settings.setValue('timeformat', core.TIMEFORMAT)
        self.settings.setValue('precision', core.PRECISION)
        self.settings.setValue('showplotter', core.SHOWPLOTTER)
        self.settings.setValue('plotstyle', core.PLOTSTYLE)
        self.settings.setValue('dpi', core.DPI)
        self.settings.setValue('recent_files',','.join(self.recent_files))
        self.settings.setValue('recent_urls','^^'.join(self.recent_urls))
        if hasattr(self, 'scratchpad'):
            self.settings.setValue('scratchpad_size',self.scratchpad.size())
        self.settings.sync()
        return

    def applySettings(self):
        """Apply settings to GUI when changed"""

        self.setIconSize(QtCore.QSize(core.ICONSIZE, core.ICONSIZE))
        for s in self.sheets:
            table = self.sheets[s]
            table.toolbar.setIconSize(QtCore.QSize(core.ICONSIZE, core.ICONSIZE))
        import matplotlib as mpl
        mpl.rcParams['savefig.dpi'] = core.DPI
        self.setTheme(self.theme)
        return

    def setTheme(self, theme=None):
        """Change interface theme."""

        app = QApplication.instance()
        if theme == None:
            theme = self.theme
        else:
            self.theme = theme
        app.setStyle(QStyleFactory.create(theme))
        self.setStyleSheet('')

        if theme in ['dark','light']:
            f = open(os.path.join(stylepath,'%s.qss' %theme), 'r')
            self.style_data = f.read()
            f.close()
            self.setStyleSheet(self.style_data)
        return

    def createToolBar(self):
        """Create main toolbar"""

        items = {'new project': {'action': lambda: self.newProject(ask=True),'file':'project-new'},
                 'open': {'action':self.openProject,'file':'document-open'},
                 'save': {'action': lambda: self.saveProject(None),'file':'save'},
                 'zoom out': {'action':self.zoomOut,'file':'zoom-out'},
                 'zoom in': {'action':self.zoomIn,'file':'zoom-in'},
                 'decrease columns': {'action': lambda: self.changeColumnWidths(.9),'file':'decrease-width'},
                 'increase columns': {'action': lambda: self.changeColumnWidths(1.1),'file':'increase-width'},
                 'add sheet': {'action': lambda: self.addSheet(name=None),'file':'add'},
                 'add column': {'action': lambda: self._call('addColumn'),'file':'add-column'},
                 'add row': {'action': lambda: self._call('addRows'),'file':'add-row'},
                 'clean data': {'action':lambda: self._call('cleanData'),'file':'clean'},
                 'table to text': {'action':lambda: self._call('showAsText'),'file':'tabletotext'},
                 'table info': {'action':lambda: self._call('info'),'file':'tableinfo'},
                 'send plot to scratchpad': {'action': self.plotToScratchpad,'file':'scratchpad-plot'},
                 'scratchpad': {'action': self.showScratchpad,'file':'scratchpad'},
                 'preferences': {'action':self.preferences,'file':'preferences-system'},
                 'quit': {'action':self.fileQuit,'file':'application-exit'}
                }

        toolbar = QToolBar("Main Toolbar")
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
        """Main menu"""

        self.file_menu = QMenu('&File', self)
        icon = QIcon(os.path.join(iconpath,'document-new.png'))
        self.file_menu.addAction(icon, '&New', lambda: self.newProject(ask=True),
                QtCore.Qt.CTRL + QtCore.Qt.Key_N)
        icon = QIcon(os.path.join(iconpath,'open.png'))
        self.file_menu.addAction(icon, '&Open', self.openProject,
                QtCore.Qt.CTRL + QtCore.Qt.Key_O)
        self.recent_files_menu = QMenu("Recent Projects",
            self.file_menu)
        self.file_menu.addAction(self.recent_files_menu.menuAction())
        icon = QIcon(os.path.join(iconpath,'save.png'))
        self.file_menu.addAction(icon, '&Save', self.saveProject,
                QtCore.Qt.CTRL + QtCore.Qt.Key_S)
        self.file_menu.addAction('&Save As', self.saveAsProject)
        self.file_menu.addAction('Import CSV file', self.importFile)
        self.file_menu.addAction('Import Multiple', self.importMultiple)
        self.file_menu.addAction('Import Pickle file', self.importPickle)
        self.file_menu.addAction('Import HDF5', self.importHDF)
        self.file_menu.addAction('Import URL', self.importURL)
        self.file_menu.addAction('Export As', self.exportAs)
        icon = QIcon(os.path.join(iconpath,'application-exit.png'))
        self.file_menu.addAction(icon, '&Quit', self.fileQuit,
                QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.edit_menu = QMenu('Edit', self)
        self.menuBar().addMenu(self.edit_menu)
        self.undo_item = self.edit_menu.addAction('Undo', self.undo,
                QtCore.Qt.CTRL + QtCore.Qt.Key_Z)
        #self.undo_item.setDisabled(True)
        icon = QIcon(os.path.join(iconpath,'copy.png'))
        self.edit_menu.addAction(icon, 'Copy', self.copy)
        icon = QIcon(os.path.join(iconpath,'paste.png'))
        self.edit_menu.addAction(icon, 'Paste', self.paste)
        icon = QIcon(os.path.join(iconpath,'paste.png'))
        self.edit_menu.addAction(icon, 'Paste as New Sheet', self.pasteNewSheet)
        icon = QIcon(os.path.join(iconpath,'findreplace.png'))
        self.edit_menu.addAction(icon, 'Find/Replace', self.findReplace,
                QtCore.Qt.CTRL + QtCore.Qt.Key_F)
        icon = QIcon(os.path.join(iconpath,'preferences-system.png'))
        self.edit_menu.addAction(icon, 'Preferences', self.preferences)

        self.view_menu = QMenu('View', self)
        self.menuBar().addMenu(self.view_menu)
        icon = QIcon(os.path.join(iconpath,'zoom-in.png'))
        self.view_menu.addAction(icon, 'Zoom In', self.zoomIn,
                QtCore.Qt.CTRL + QtCore.Qt.Key_Equal)
        icon = QIcon(os.path.join(iconpath,'zoom-out.png'))
        self.view_menu.addAction(icon, 'Zoom Out', self.zoomOut,
                QtCore.Qt.CTRL + QtCore.Qt.Key_Minus)
        icon = QIcon(os.path.join(iconpath,'decrease-width.png'))
        self.view_menu.addAction(icon, 'Decrease Column Width', lambda: self.changeColumnWidths(.9))
        icon = QIcon(os.path.join(iconpath,'increase-width.png'))
        self.view_menu.addAction(icon, 'Increase Column Width', self.changeColumnWidths)
        icon = QIcon(os.path.join(iconpath,'preferences-system.png'))
        action=self.view_menu.addAction(icon, 'Show Plotter', self.showPlotFrame)
        action.setCheckable(True)

        self.theme_menu = QMenu("Themes",  self.view_menu)
        #group = QActionGroup(self.theme_menu)
        #group.setExclusive(True)
        themes = QStyleFactory.keys()
        for t in themes:
            self.theme_menu.addAction(t, lambda t=t: self.setTheme(t))
            #group.addAction(action)
        self.theme_menu.addAction('Dark', lambda: self.setTheme('dark'))
        self.theme_menu.addAction('Light', lambda: self.setTheme('light'))
        self.view_menu.addAction(self.theme_menu.menuAction())

        self.sheet_menu = QMenu('Sheet', self)
        self.menuBar().addMenu(self.sheet_menu)
        icon = QIcon(os.path.join(iconpath,'add.png'))
        self.sheet_menu.addAction(icon, 'Add', self.addSheet)
        self.sheet_menu.addAction('Rename', self.renameSheet)
        icon = QIcon(os.path.join(iconpath,'copy.png'))
        #self.sheet_menu.addAction(icon, 'Copy', self.copySheet)
        self.sheet_menu.addAction(icon, 'Duplicate', self.duplicateSheet)
        self.sheet_menu.addAction('Join', self.concatSheets)
        icon = QIcon(os.path.join(iconpath,'merge.png'))
        self.sheet_menu.addAction(icon, 'Merge', self.mergeSheets)
        self.sheet_menu.addAction('Clear All', self.clearSheets)

        self.tools_menu = QMenu('Tools', self)
        icon = QIcon(os.path.join(iconpath,'tableinfo.png'))
        self.tools_menu.addAction(icon, '&Table Info', lambda: self._call('info'),
                QtCore.Qt.CTRL + QtCore.Qt.Key_I)
        self.tools_menu.addAction('Manage Columns', lambda: self._call('manageColumns'))
        icon = QIcon(os.path.join(iconpath,'clean.png'))
        self.tools_menu.addAction(icon, 'Clean Data', lambda: self._call('cleanData'))
        icon = QIcon(os.path.join(iconpath,'table-duplicates.png'))
        self.tools_menu.addAction(icon, 'Find Duplicates', lambda: self._call('findDuplicates'))
        self.tools_menu.addAction('Convert Numeric', lambda: self._call('convertNumeric'))
        self.tools_menu.addAction('Format Column Names', lambda: self._call('convertColumnNames'))
        self.tools_menu.addAction('Time Series Resample', lambda: self._call('resample'))
        icon = QIcon(os.path.join(iconpath,'tabletotext.png'))
        self.tools_menu.addAction(icon, '&Table to Text', lambda: self._call('showAsText'),
                QtCore.Qt.CTRL + QtCore.Qt.Key_T)
        icon = QIcon(os.path.join(iconpath,'interpreter.png'))
        self.tools_menu.addAction(icon, 'Python Interpreter', self.interpreter)
        self.menuBar().addMenu(self.tools_menu)

        self.dataset_menu = QMenu('Datasets', self)
        self.menuBar().addMenu(self.dataset_menu)
        self.dataset_menu.addAction('Sample', lambda: self.getSampleData('sample'))
        self.dataset_menu.addAction('Iris', lambda: self.getSampleData('iris'))
        self.dataset_menu.addAction('Titanic', lambda: self.getSampleData('titanic'))
        self.dataset_menu.addAction('Pima Diabetes', lambda: self.getSampleData('pima'))

        self.scratch_menu = QMenu('Scratchpad', self)
        self.menuBar().addMenu(self.scratch_menu)
        icon = QIcon(os.path.join(iconpath,'scratchpad.png'))
        self.scratch_menu.addAction(icon,'Show Scratchpad', lambda: self.showScratchpad())
        icon = QIcon(os.path.join(iconpath,'scratchpad-plot.png'))
        self.scratch_menu.addAction(icon,'Plot to Scratchpad', lambda: self.plotToScratchpad())
        icon = QIcon(os.path.join(iconpath,'scratchpad-table.png'))
        self.scratch_menu.addAction(icon,'Table to Scratchpad', lambda: self.tableToScratchpad())

        self.plugin_menu = QMenu('Plugins', self)
        self.menuBar().addMenu(self.plugin_menu)

        self.dock_menu = QMenu('Docks', self)
        self.menuBar().addMenu(self.dock_menu)

        self.help_menu = QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)
        self.help_menu.addAction('View Error Log', self.showErrorLog)
        url = 'https://tablexplore.readthedocs.io/en/latest/'
        self.help_menu.addAction('Online Help', lambda: self.open_url(url))
        icon = QIcon(os.path.join(iconpath,'logo.png'))
        self.help_menu.addAction(icon, 'About', self.about)

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

        fname = os.path.abspath(fname)
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
            elif reply == QMessageBox.Cancel:
                return
        if not type(data) is dict:
            data = None
        #clear tabs
        self.tabs.clear()
        self.sheets = OrderedDict()
        self.filename = None
        self.projopen = True
        self.scratch_items = {}
        #load data if provided
        if data != None:
            for s in data.keys():
                if s in ['meta','scratch_items']:
                    continue
                df = data[s]['table']
                if 'meta' in data[s]:
                    meta = data[s]['meta']
                else:
                    meta=None
                self.addSheet(s, df, meta)
            if 'scratch_items' in data:
                self.scratch_items = data['scratch_items']
            #set current sheet
            if 'meta' in data:
                self.tabs.setCurrentIndex(data['meta']['currentsheet'])
        else:
            self.addSheet('dataset1')
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
                                  homepath,"tablexplore Files (*.txpl);;All files (*.*)",
                                  options=options)

        if not filename:
            return
        if not os.path.exists(filename):
            print ('no such file')
            #self.removeRecent(filename)
            return
        ext = os.path.splitext(filename)[1]
        if ext != '.txpl':
            print ('does not appear to be a project file')
            return
        if os.path.isfile(filename):
            try:
                data = pickle.load(gzip.GzipFile(filename, 'r'))
            except Exception as e:
                print ('Could not load pickle file')
                msg = 'Could not load pickle file. Possibly this was saved with an older version of Python.'
                dialogs.showMessage(self, msg)
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
                                                  homepath,"tablexplore Files (*.txpl);;All files (*.*)",
                                                  options=options)
        if not filename:
            return

        if not os.path.splitext(filename)[1] == '.txpl':
            filename += '.txpl'
        self.filename = filename
        self.do_saveProject(filename)
        self.addRecentFile(filename)
        self.proj_label.setText(self.filename)
        return

    def saveProject(self, filename=None):
        """Save project"""

        if self.filename != None:
            filename = self.filename
        if filename is None:
            self.saveAsProject()
        #if not os.path.splitext(filename)[1] == '.txpl':
        #    filename += '.txpl'
        if not filename:
            return
        self.running = True
        if not os.path.splitext(filename)[1] == '.txpl':
            filename += '.txpl'
        self.filename = filename
        self.defaultsavedir = os.path.dirname(os.path.abspath(filename))
        self.saveWithProgress(self.filename)
        return

    def saveWithProgress(self, filename):
        """Save with progress bar"""

        self.savedlg = dlg = dialogs.ProgressWidget(label='Saving to %s' %filename)
        dlg.show()
        def func(progress_callback):
            self.do_saveProject(self.filename)
        self.run_threaded_process(func, self.processing_completed)
        return

    def run_threaded_process(self, process, on_complete):
        """Execute a function in the background with a worker"""

        #if self.running == True:
        #    return
        worker = dialogs.Worker(fn=process)
        self.threadpool.start(worker)
        worker.signals.finished.connect(on_complete)
        #worker.signals.progress.connect(self.progress_fn)
        self.savedlg.progressbar.setRange(0,0)
        #self.worker = worker
        return

    def progress_fn(self, msg):
        return

    def processing_completed(self):
        """Generic process completed"""

        self.savedlg.progressbar.setRange(0,1)
        self.savedlg.close()
        self.running = False
        return

    def do_saveProject(self, filename, progress_callback=None):
        """Does the actual saving. Save sheets inculding table dataframes
           and meta data as dict to compressed pickle.
        """

        data={}
        for i in self.sheets:
            tablewidget = self.sheets[i]
            table = tablewidget.table
            data[i] = {}
            #save dataframe with current column order
            if table.filtered == True:
                table.showAll()

            df = table.model.df
            cols = table.getColumnOrder()
            if table.checkColumnsUnique() == True:
                df = df[cols]
            data[i]['table'] = df
            data[i]['meta'] = self.saveMeta(tablewidget)

        data['scratch_items'] = self.scratch_items
        data['meta'] = {}
        data['meta']['currentsheet'] = self.tabs.currentIndex()
        file = gzip.GzipFile(filename, 'w')
        pickle.dump(data, file)
        return

    def saveMeta(self, tablewidget):
        """Save meta data such as current plot options and certain table attributes.
         These are re-loaded when the sheet is opened."""

        meta = {}
        pf = tablewidget.pf
        #pf.applyPlotoptions()
        table = tablewidget.table
        #save plot options
        meta['opts'] = {}
        for name in pf.opts:
            meta['opts'][name] = pf.opts[name].kwds
            #print (pf.opts[name].kwds)

        #save table selections
        meta['table'] = util.getAttributes(table)
        meta['table']['selectedcols'] = table.getSelectedColumns()
        meta['table']['selectedrows'] = table.getSelectedRows()
        meta['table']['scrollposition'] = table.getScrollPosition()
        meta['table']['filtered'] = False
        meta['table']['column_widths'] = table.getColumnWidths()
        meta['plotviewer'] = util.getAttributes(pf)
        #print (meta['plotviewer'])
        #is plotter shown
        if pf.isHidden():
            meta['showplotter'] = False
        else:
            meta['showplotter'] = True
        #save child table if present
        if tablewidget.subtable != None:
            meta['subtable'] = tablewidget.subtable.table.model.df

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
        opts = table.pf.opts
        for name in opts:
            #if m in meta and meta[m] is not None:
            #opts[name].updateWidgets(meta['opts'][name])
            opts[name].kwds = meta['opts'][name]
            self.updatePlotWidgets(table)

        #load table settings
        util.setAttributes(table.table, tablesettings)
        #print (tablesettings)
        if 'column_widths' in tablesettings:
            #print (len(tablesettings['column_widths']))
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

        #redraw selections
        if 'selectedrows' in tablesettings:
            rows = tablesettings['selectedrows']
            cols = tablesettings['selectedcols']
            table.table.setSelected(rows, cols)
        #move to scroll position
        if 'scrollposition' in tablesettings:
            row,col = tablesettings['scrollposition']
            table.table.setScrollPosition(row, col)
        return

    def importFile(self, filename=None):

        self.addSheet()
        w = self.getCurrentTable()
        w.importFile(filename, dialog=True)
        return

    def importMultiple(self):
        """Import many files"""

        options = QFileDialog.Options()
        filenames, _ = QFileDialog.getOpenFileNames(self,"Import Files",
                             "","CSV files (*.csv);;Text Files (*.txt);;All Files (*)",
                             options=options)
        if not filenames:
            return

        for f in filenames:
            name = os.path.splitext(os.path.basename(f))[0]
            if name in self.sheets:
                name+='_1'
            self.addSheet(name)
            w = self.getCurrentTable()
            w.importFile(f, dialog=False)

        return

    def importExcel(self, filename=None):

        self.addSheet()
        w = self.getCurrentTable()
        w.importExcel(filename)
        return

    def importPickle(self):

        self.addSheet()
        w = self.getCurrentTable()
        w.importPickle()
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

        names = list(self.sheets.keys())
        i=len(self.sheets)+1
        if name == None or name in names:
            name = 'dataset'+str(i)
        if name in names:
            import random
            name = 'dataset'+str(random.randint(i,100))

        sheet = QSplitter(self.tabs)
        sheet.setStyleSheet(splittercss)
        idx = self.tabs.addTab(sheet, name)
        #provide reference to self to dataframewidget
        dfw = DataFrameWidget(sheet, dataframe=df, app=self,
                                font=core.FONT, fontsize=core.FONTSIZE, bg=core.BGCOLOR,
                                columnwidth=core.COLUMNWIDTH, timeformat=core.TIMEFORMAT)
        sheet.addWidget(dfw)
        self.sheets[name] = dfw
        self.currenttable = dfw
        pf = dfw.createPlotViewer(sheet)
        sheet.addWidget(pf)
        sheet.setSizes((500,1000))

        #reload attributes of table and plotter if present
        if meta != None:
            self.loadMeta(dfw, meta)
            if core.SHOWPLOTTER == False:
                pf.hide()
            if 'showplotter' in meta and meta['showplotter'] == False:
                pf.hide()

        self.updatePlotWidgets(dfw)
        self.updatePlugins()
        self.tabs.setCurrentIndex(idx)
        return

    def removeSheet(self, index, ask=True):
        """Remove sheet"""

        if ask == True:
            reply = QMessageBox.question(self, 'Delete this sheet?',
                                 'Are you sure?', QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.No:
                return False
        name = self.tabs.tabText(index)
        del self.sheets[name]
        self.tabs.removeTab(index)
        return

    def renameSheet(self):
        """Rename the current sheet"""

        if len(self.sheets) == 0:
            return
        index = self.tabs.currentIndex()
        name = self.tabs.tabText(index)
        new, ok = QInputDialog.getText(self, 'New name', 'Name:',
                    QLineEdit.Normal, name)
        if ok:
            if new in self.sheets:
                QMessageBox.information(self, "Cannot rename",
                                    "Sheet name already present")
                return
            self.sheets[new] = self.sheets[name]
            del self.sheets[name]
            self.tabs.setTabText(index, new)
        return

    def duplicateSheet(self):
        """Make a copy of a sheet"""

        if len(self.sheets) == 0:
            return
        index = self.tabs.currentIndex()
        name = self.tabs.tabText(index)
        df = self.sheets[name].table.model.df.copy()
        meta = self.saveMeta(self.sheets[name])
        new, ok = QInputDialog.getText(self, 'New name', 'Name:',
                    QLineEdit.Normal, name+'_copy')
        if ok:
            self.addSheet(new, df, meta=meta)
        return

    def concatSheets(self):
        """Combine sheets into one table"""

        if len(self.sheets) == 0:
            return
        names = self.sheets.keys()
        if len(names) < 2:
            return
        ops=['concat']
        opts = {'sheets':{'type':'list','default':'','items':names},
                'new name':{'type':'entry','default':'combined'},
                'add label column':{'type':'checkbox','default':False},
                }
        dlg = dialogs.MultipleInputDialog(self, opts, title='Combine',
                            width=250,height=150)
        dlg.exec_()
        if not dlg.accepted:
            return
        kwds = dlg.values

        names = kwds['sheets']
        lblcol = kwds['add label column']
        new = []
        for n in names:
            df = self.sheets[n].table.model.df
            if lblcol == True:
                df['label'] = n
            new.append(df)
        new = pd.concat(new)
        label = kwds['new name']
        self.addSheet(label,df=new)
        return

    def mergeSheets(self):
        """Merge two sheets"""

        if len(self.sheets) < 2:
            return
        names = self.sheets.keys()
        opts = {'sheet1':{'type':'combobox','default':'','items':names},
                'sheet2':{'type':'combobox','default':'','items':names}
                }
        dlg = dialogs.MultipleInputDialog(self, opts, title='Merge sheets',
                            width=250,height=150)
        dlg.exec_()
        if not dlg.accepted:
            return
        kwds = dlg.values
        table1 = self.sheets[kwds['sheet1']].table
        table2 = self.sheets[kwds['sheet2']].table
        dlg = dialogs.MergeDialog(self, df=table1.model.df, df2=table2.model.df, app=self)
        dlg.exec_()
        if not dlg.accepted:
            return
        return

    def clearSheets(self, ask=True):
        """Clear all sheets"""

        if ask == True:
            reply = QMessageBox.question(self, 'Clear all sheets?',
                                 'This will remove all sheets. Are you sure?',
                                 QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.No:
                return
        self.tabs.clear()
        self.sheets = {}
        return

    def showPlotFrame(self):
        """Show/hide the plot frame"""

        index = self.tabs.currentIndex()
        name = self.tabs.tabText(index)
        pf = self.sheets[name].pf
        if pf.isHidden():
            pf.show()
            #pf.dock.show()
        else:
            pf.hide()
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

    def closeEvent(self, event):
        """Close event"""

        reply = QMessageBox.question(self, 'Close',
                                 'Save current project?',
                                  QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        if reply == QMessageBox.Cancel:
            event.ignore()
            return
        if reply == QMessageBox.Yes:
            self.saveProject()

        for s in self.sheets:
            self.sheets[s].close()
        self.saveSettings()
        if hasattr(self,'scratchpad'):
            self.scratchpad.close()
        self.threadpool.waitForDone()
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
                        'cols':{'type':'spinbox','default':5,'range':(1,100)},
                        'n':{'type':'spinbox','default':2,'range':(1,30),'label':'name length'},}
                dlg = dialogs.MultipleInputDialog(self, opts, title='Sample data',
                                    width=250,height=150)
                dlg.exec_()
                if not dlg.accepted:
                    return
                kwds = dlg.values
                rows = kwds['rows']
                cols = kwds['cols']
                n = kwds['n']
            if ok:
                df = util.getSampleData(rows,cols,n)
            else:
                return
        else:
            df = util.getPresetData(name)
        self.addSheet(sheetname,df)
        return

    def getCurrentTable(self):
        """Return the currently used table"""

        idx = self.tabs.currentIndex()
        name = self.tabs.tabText(idx)
        table = self.sheets[name]
        return table

    def copy(self):
        w = self.getCurrentTable()
        w.copy()
        return

    def paste(self):
        w = self.getCurrentTable()
        w.paste()
        return

    def pasteNewSheet(self):

        self.addSheet()
        self.paste()
        return

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

    '''def runLastAction(self):
        w = self.getCurrentTable()
        w.runLastAction()
        return'''

    def findReplace(self):
        """Find or replace"""

        w = self.getCurrentTable()
        w.findreplace()
        return

    def refresh(self):
        """Refresh all tables"""

        for s in self.sheets:
            w = self.sheets[s].table
            w.font = core.FONT
            w.fontsize = core.FONTSIZE
            w.model.bg = core.BGCOLOR
            w.refresh()
        return

    def tableToScratchpad(self):
        """Send table selection to scratchpad"""

        w = self.getCurrentTable()
        index = self.tabs.currentIndex()
        name = self.tabs.tabText(index)
        df = w.getSelectedDataFrame()
        t = time.strftime("%H:%M:%S")
        label = name+'-'+t
        self.scratch_items[label] = df
        if hasattr(self, 'scratchpad'):
            self.scratchpad.update(self.scratch_items)
        return

    def plotToScratchpad(self, label=None):
        """Cache the current plot so it can be viewed later"""

        w = self.getCurrentTable()
        if label == None or label is False:
            index = self.tabs.currentIndex()
            name = self.tabs.tabText(index)
            t = time.strftime("%H:%M:%S")
            label = name+'-'+t
        #get the current figure and make a copy of it by using pickle
        fig = w.pf.fig
        p = pickle.dumps(fig)
        fig = pickle.loads(p)

        self.scratch_items[label] = fig
        if hasattr(self, 'scratchpad'):
            self.scratchpad.update(self.scratch_items)
        return

    def showScratchpad(self):
        """Show stored plot figures"""

        from . import plotting
        if not hasattr(self, 'scratchpad'):
            self.scratchpad = widgets.ScratchPad()
            try:
                self.scratchpad.resize(self.settings.value('scratchpad_size'))
            except:
                pass
        self.scratchpad.update(self.scratch_items)
        self.scratchpad.show()
        self.scratchpad.activateWindow()
        return

    def interpreter(self):
        """Launch python interpreter"""

        table = self.getCurrentTable()
        table.showInterpreter()
        return

    def discoverPlugins(self):
        """Discover available plugins"""

        from . import plugin
        default = os.path.join(module_path, 'plugins')
        other = os.path.join(core.settingspath, 'plugins')
        paths = [default,other]
        failed = plugin.init_plugin_system(paths)
        self.updatePluginMenu()
        return

    def loadPlugin(self, plugin):
        """Instantiate the plugin and call it's main method"""

        index = self.tabs.currentIndex()
        name = self.tabs.tabText(index)
        tablew = self.sheets[name]
        if not hasattr(self, 'openplugins'):
            self.openplugins = {}
        openplugins = self.openplugins

        if plugin.name in openplugins:
            p = openplugins[plugin.name]
            self.docks[plugin.name].show()
        else:
            try:
                p = plugin(parent=self, table=tablew)
                #track which plugin is running
                openplugins[plugin.name] = p
            except Exception as e:
                QMessageBox.information(self, "Plugin error", str(e))
                return

            #plugin should be added as a dock widget
            self.showPlugin(p)
        return

    def showPlugin(self, plugin):
        """Add plugin as dock widget"""

        dockstyle = '''
            QDockWidget::title {
                background-color: #d7edce;
            }
        '''
        dock = QDockWidget(plugin.name)
        dock.setStyleSheet(dockstyle)
        area = QScrollArea()
        area.setWidgetResizable(True)
        dock.setWidget(area)
        area.setWidget(plugin.main)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)
        self.docks[plugin.name] = dock
        return

    def updatePluginMenu(self):
        """Update plugins"""

        from . import plugin
        plgmenu = self.plugin_menu
        for plg in plugin.get_plugins_classes('gui'):

            def func(p, **kwargs):
                def new():
                   self.loadPlugin(p)
                return new
            if hasattr(plg,'iconfile'):
                icon = QIcon(os.path.join(pluginiconpath,plg.iconfile))
                plgmenu.addAction(icon, plg.menuentry, func(plg))
            else:
                plgmenu.addAction(plg.menuentry, func(plg))
        return

    def preferences(self):
        """Preferences dialog"""

        from . import dialogs
        opts = {}
        for k in core.defaults.keys():
            opts[k] = getattr(core,k)
        opts['THEME'] = self.theme
        dlg = dialogs.PreferencesDialog(self, opts)
        dlg.exec_()
        return

    def showErrorLog(self):
        """Show log file contents"""

        f = open(self.logfile,'r')
        s = ''.join(f.readlines())
        dlg = dialogs.TextDialog(self, s, title='Log', width=800, height=400)
        dlg.exec_()
        return

    def open_url(self,url='',event=None):
        """Open the online documentation"""

        import webbrowser
        webbrowser.open(url,autoraise=1)
        return

    def about(self):
        from . import __version__
        import matplotlib

        pandasver = pd.__version__
        pythonver = platform.python_version()
        mplver = matplotlib.__version__
        if 'PySide2' in sys.modules:
            import PySide2
            qtver = 'PySide2='+PySide2.QtCore.__version__
        else:
            import PyQt5
            qtver = 'PyQt5='+ PyQt5.QtCore.QT_VERSION_STR

        text='Tablexplore Application\n'\
                +'Version '+__version__+'\n'\
                +'Copyright (C) Damien Farrell 2018-\n'\
                +'This program is free software; you can redistribute it and/or\n'\
                +'modify it under the terms of the GNU General Public License '\
                +'as published by the Free Software Foundation; either version 3 '\
                +'of the License, or (at your option) any later version.\n'\
                +'Using Python v%s, %s\n' %(pythonver, qtver)\
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
    parser.add_argument("-x", "--excel", dest="excel_file",
                        help="Import an excel file", metavar="FILE")
    args = vars(parser.parse_args())

    app = QApplication(sys.argv)
    aw = Application(**args)
    aw.show()
    app.exec_()

if __name__ == '__main__':
    main()

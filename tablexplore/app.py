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
import sys,os,platform
import pickle, gzip
from collections import OrderedDict
from PySide2 import QtCore
from PySide2.QtWidgets import *
from PySide2.QtGui import *
import pandas as pd
from .core import DataFrameModel, DataFrameTable, DataFrameWidget
from .plotting import PlotViewer
from . import util, data

homepath = os.path.expanduser("~")
module_path = os.path.dirname(os.path.abspath(__file__))
stylepath = os.path.join(module_path, 'styles')

class Application(QMainWindow):
    def __init__(self, project_file=None, csv_file=None):

        QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Tablexplore")
        self.setWindowIcon(QIcon('logo.png'))

        self.createMenu()
        self.main = QTabWidget(self)
        self.main.setTabsClosable(True)
        self.main.tabCloseRequested.connect(lambda index: self.removeSheet(index))
        screen_resolution = QGuiApplication.primaryScreen().availableGeometry()
        width, height = screen_resolution.width()*0.7, screen_resolution.height()*.7
        self.setGeometry(QtCore.QRect(200, 200, width, height))

        self.newProject()
        self.main.setFocus()
        self.setCentralWidget(self.main)
        self.statusbar = QStatusBar()
        #self.statusbar.addWidget(lbl,1)
        self.proj_label = QLabel("")
        self.statusbar.addWidget(self.proj_label, 1)
        self.proj_label.setStyleSheet('color: blue')

        #self.statusBar().showMessage("Welcome", 3000)
        self.setStatusBar(self.statusbar)
        if project_file != None:
            self.openProject(project_file)
        elif csv_file != None:
            self.import_file(csv_file)
        self.loadSettings()
        #self.setStyle()
        return

    def loadSettings(self):
        """Load GUI settings"""

        s = self.settings = QtCore.QSettings('tablexplore','default')
        #self.settings.setValue("RecentFiles", recentFiles)
        print(QStyleFactory.keys())
        #self.setStyle(QStyleFactory.create('Fusion'))
        self.recentFiles = s.value("RecentFiles")
        try:
            self.resize(s.value('window size'))
            self.move(s.value('window position'))
            print ('set')
        except:
            pass

        return

    def saveSettings(self):
        """Save GUI settings"""

        self.settings.setValue('window size', self.size())
        self.settings.setValue('window position', self.pos())
        self.settings.sync()
        return

    def setStyle(self):

        f = open(os.path.join(stylepath,'light.qss'), 'r')
        self.style_data = f.read()
        f.close()
        self.setStyleSheet(self.style_data)
        return

    def createMenu(self):

        self.file_menu = QMenu('&File', self)
        self.file_menu.addAction('&New', self.newProject,
                QtCore.Qt.CTRL + QtCore.Qt.Key_N)
        self.file_menu.addAction('&Open', self.openProject,
                QtCore.Qt.CTRL + QtCore.Qt.Key_O)
        self.menuRecentFiles = QMenu("Open Recent Files",
            self.file_menu)
        self.file_menu.addAction(self.menuRecentFiles.menuAction())
        self.file_menu.addAction('&Save', self.saveProject,
                QtCore.Qt.CTRL + QtCore.Qt.Key_S)
        self.file_menu.addAction('&Save As', self.saveAsProject)
        self.file_menu.addAction('&Import', self.import_file)
        self.file_menu.addAction('&Quit', self.fileQuit,
                QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.edit_menu = QMenu('&Edit', self)
        self.menuBar().addMenu(self.edit_menu)
        self.edit_menu.addAction('&Undo', self.undo)

        self.view_menu = QMenu('&View', self)
        self.menuBar().addMenu(self.view_menu)
        self.view_menu.addAction('&Zoom In', self.zoomIn,
                QtCore.Qt.CTRL + QtCore.Qt.Key_Equal)
        self.view_menu.addAction('&Zoom Out', self.zoomOut,
                QtCore.Qt.CTRL + QtCore.Qt.Key_Minus)

        self.sheet_menu = QMenu('&Sheet', self)
        self.menuBar().addMenu(self.sheet_menu)
        self.sheet_menu.addAction('&Add', self.addSheet)
        self.sheet_menu.addAction('&Rename', self.renameSheet)
        self.sheet_menu.addAction('&Copy', self.copySheet)

        self.tools_menu = QMenu('&Tools', self)
        self.tools_menu.addAction('&Table Info', lambda: self._call('info'),
                QtCore.Qt.CTRL + QtCore.Qt.Key_I)
        self.tools_menu.addAction('&Clean Data', lambda: self._call('cleanData'),
                QtCore.Qt.CTRL + QtCore.Qt.Key_D)
        self.tools_menu.addAction('&Convert Numeric', lambda: self._call('convertNumeric'))
        self.tools_menu.addAction('&Convert Column Names', lambda: self._call('convertColumnNames'))
        self.tools_menu.addAction('&Table to Text', lambda: self._call('showAsText'),
                QtCore.Qt.CTRL + QtCore.Qt.Key_T)
        self.menuBar().addMenu(self.tools_menu)

        self.dataset_menu = QMenu('&Datasets', self)
        self.menuBar().addMenu(self.dataset_menu)
        self.dataset_menu.addAction('&Sample', lambda: self.getSampleData('sample'))
        self.dataset_menu.addAction('&Iris', lambda: self.getSampleData('iris'))

        self.help_menu = QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)
        self.help_menu.addAction('&About', self.about)
        return

    def _call(self, func, **args):
        """Call a table function from it's string name"""

        table = self.get_current_table()
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

    def addRecentFile(self, fname):

        if fname and fname not in self.recentFiles:
            self.recentFiles.insert(0, fname)
            if len(self.recentFiles) > 9:
                self.recentFiles = self.recentFiles[:9]
        self.menuRecentFiles.setEnabled(len(self.recentFiles))
        return

    def newProject(self, data=None):
        """New project"""

        self.main.clear()
        self.sheets = OrderedDict()
        self.filename = None
        self.projopen = True
        if data != None:
            for s in sorted(data.keys()):
                if s == 'meta':
                    continue
                df = data[s]['table']
                if 'meta' in data[s]:
                    meta = data[s]['meta']
                else:
                    meta=None
                self.addSheet(s, df, meta)
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
        #self.addRecentFile(filename)
        return

    def saveAsProject(self):

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
        """Save as a new filename"""

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
        return

    def do_saveProject(self, filename):
        """Save sheets as dict to pickle"""

        data={}
        for i in self.sheets:
            #print (i)
            tablewidget = self.sheets[i]
            table = tablewidget.table
            data[i] = {}
            data[i]['table'] = table.model.df
            #data[i]['meta'] = self.saveMeta(tablewidget)

        file = gzip.GzipFile(filename, 'w')
        pickle.dump(data, file)
        return

    def saveMeta(self, tablewidget):
        """Save meta data such as current plot options"""

        meta = {}
        pf = tablewidget.pf
        table =  tablewidget.table
        #save plot options
        meta['generalopts'] = pf.generalopts.kwds
        #meta['mplopts3d'] = pf.mplopts3d.kwds
        meta['labelopts'] = pf.labelopts.kwds

        #save table selections
        meta['table'] = util.getAttributes(table)
        meta['plotviewer'] = util.getAttributes(pf)
        #print (meta['plotviewer'])
        #save row colors since its a dataframe and isn't picked up by getattributes currently
        #meta['table']['rowcolors'] = table.rowcolors

        #save child table if present
        #if table.child != None:
        #    meta['childtable'] = table.child.model.df
        #    meta['childselected'] = util.getAttributes(table.child)

        return meta

    def import_file(self, filename=None):

        self.addSheet()
        w = self.get_current_table()
        w.importFile(filename)
        return

    def addSheet(self, name=None, df=None, meta=None):
        """Add a new sheet"""

        names = self.sheets.keys()
        if name is None:
            name = 'dataset'+str(len(self.sheets)+1)

        sheet = QSplitter(self.main)
        idx = self.main.addTab(sheet, name)
        #provide reference to self to dataframewidget
        dfw = DataFrameWidget(sheet, dataframe=df, app=self)
        sheet.addWidget(dfw)

        self.sheets[name] = dfw
        self.currenttable = dfw
        pf = dfw.createPlotViewer(sheet)
        sheet.addWidget(pf)
        sheet.setSizes((500,1000))
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
        self.saveSettings()
        self.fileQuit()

    def getSampleData(self, name, rows=None):
        """Sample table"""

        ok = True
        if name == 'sample':
            if rows is None:
                rows, ok = QInputDialog.getInt(self, 'Rows', 'Rows:', 100)
            if ok:
                df = data.getSampleData(rows,5)
        else:
            df = data.getIrisData()
        self.addSheet(None,df)
        return

    def get_current_table(self):

        idx = self.main.currentIndex()
        name= self.main.tabText(idx)

        table = self.sheets[name]
        return table

    def zoomIn(self):

        w = self.get_current_table()
        w.table.zoomIn()
        return

    def zoomOut(self):

        w = self.get_current_table()
        w.table.zoomOut()
        return

    def undo(self):

        return

    def online_documentation(self,event=None):
        """Open the online documentation"""
        import webbrowser
        link='https://pandastable.readthedocs.io/en/latest/'
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

        text='TablExplore Application\n'\
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

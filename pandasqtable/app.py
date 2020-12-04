#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
    Dataexplore2 table app
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
from . import util

class Application(QMainWindow):
    def __init__(self):

        QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("DataExplore2")
        self.setWindowIcon(QIcon('logo.png'))
        self.createMenu()
        self.main = QTabWidget(self)
        self.main.setTabsClosable(True)
        self.main.tabCloseRequested.connect(lambda index: self.main.removeTab(index))
        screen_resolution = QDesktopWidget().screenGeometry()
        width, height = screen_resolution.width()*0.7, screen_resolution.height()*.7
        self.setGeometry(QtCore.QRect(200, 200, width, height))
        center = QDesktopWidget().availableGeometry().center()
        self.new_project()
        self.sampleData(200)
        self.main.setFocus()
        self.setCentralWidget(self.main)
        self.statusBar().showMessage("Welcome", 3000)
        return

    def createMenu(self):

        self.file_menu = QMenu('&File', self)
        self.file_menu.addAction('&New', self.new_project,
                QtCore.Qt.CTRL + QtCore.Qt.Key_N)
        self.file_menu.addAction('&Open', self.openProject,
                QtCore.Qt.CTRL + QtCore.Qt.Key_O)
        self.file_menu.addAction('&Save', self.save_project,
                QtCore.Qt.CTRL + QtCore.Qt.Key_S)
        self.file_menu.addAction('&Import', self.import_file)
        self.file_menu.addAction('&Quit', self.fileQuit,
                QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.edit_menu = QMenu('&Edit', self)
        self.menuBar().addMenu(self.edit_menu)
        self.edit_menu.addAction('&Undo', self.add_sheet)

        self.view_menu = QMenu('&View', self)
        self.menuBar().addMenu(self.view_menu)
        self.view_menu.addAction('&Zoom In', self.zoomIn,
                QtCore.Qt.CTRL + QtCore.Qt.Key_Equal)
        self.view_menu.addAction('&Zoom Out', self.zoomOut,
                QtCore.Qt.CTRL + QtCore.Qt.Key_Minus)

        self.sheet_menu = QMenu('&Sheet', self)
        self.menuBar().addMenu(self.sheet_menu)
        self.sheet_menu.addAction('&Add', self.add_sheet)

        self.tools_menu = QMenu('&Tools', self)
        self.tools_menu.addAction('&Table Info', lambda: self._call('info'),
                QtCore.Qt.CTRL + QtCore.Qt.Key_I)
        self.tools_menu.addAction('&Clean Data', lambda: self._call('cleanData'),
                QtCore.Qt.CTRL + QtCore.Qt.Key_D)
        self.tools_menu.addAction('&Convert Numeric', lambda: self._call('convertNumeric'))
        self.tools_menu.addAction('&Convert Column Names', lambda: self._call('convertColumnNames'))
        self.tools_menu.addAction('&Table to Text', lambda: self._call('convertColumnNames'),
                QtCore.Qt.CTRL + QtCore.Qt.Key_T)
        self.menuBar().addMenu(self.tools_menu)

        self.dataset_menu = QMenu('&Datasets', self)
        self.menuBar().addMenu(self.dataset_menu)
        self.dataset_menu.addAction('&Sample', self.sampleData)

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

    def new_project(self, data=None):
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
                self.add_sheet(s, df, meta)
        else:
            self.add_sheet()

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
            filename, _ = QFileDialog.getOpenFileName(self,"Import File",
                                                      "","Dxpl Files (*.dexpl);;All files (*.*)",
                                                      options=options)

        if not filename:
            return
        if not os.path.exists(filename):
            print ('no such file')
            self.removeRecent(filename)
            return
        ext = os.path.splitext(filename)[1]
        if ext != '.dexpl':
            print ('does not appear to be a project file')
            return
        if os.path.isfile(filename):
            data = pickle.load(gzip.GzipFile(filename, 'r'))
        else:
            print ('no such file')
            self.quit()
            return
        self.new_project(data)
        self.filename = filename
        self.main.title('%s - DataExplore' %filename)
        self.projopen = True
        self.defaultsavedir = os.path.dirname(os.path.abspath(filename))
        #self.addRecent(filename)
        return

    def save_project(self, filename=None):
        """Save as a new filename"""

        if filename is None:
            options = QFileDialog.Options()
            filename, _ = QFileDialog.getSaveFileName(self,"Save Project",
                                                      "","Dxpl Files (*.dexpl);;All files (*.*)",
                                                      options=options)
        if not filename:
            return
        self.filename = filename
        if not os.path.splitext(filename)[1] == '.snpgenie':
            self.filename += '.dexpl'
        self.defaultsavedir = os.path.dirname(os.path.abspath(filename))
        self.do_save_project(self.filename)
        #self.addRecent(filename)
        print (self.filename)
        return

    def do_save_project(self, filename):
        """Save sheets as dict to pickle"""

        #self._checkTables()
        data={}
        for i in self.sheets:
            tablewidget = self.sheets[i]
            table = tablewidget.table
            data[i] = {}
            data[i]['table'] = table.model.df
            data[i]['meta'] = self.saveMeta(tablewidget)

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

    def import_file(self):

        self.add_sheet()
        w = self.get_current_table()
        w.importFile()
        return

    def add_sheet(self, name=None, df=None, meta=None):
        """Add a new sheet"""

        names = self.sheets.keys()
        if name is None:
            name = 'sheet'+str(len(self.sheets)+1)

        sheet = QSplitter(self.main)
        idx = self.main.addTab(sheet, name)

        l = QHBoxLayout(sheet)
        dfw = DataFrameWidget(sheet, dataframe=df)
        l.addWidget(dfw)
        self.sheets[idx] = dfw
        self.currenttable = dfw
        pf = dfw.createPlotViewer(sheet)
        l.addWidget(pf)
        sheet.setSizes((500,600))
        self.main.setCurrentIndex(idx)
        return

    def remove_sheet(self, name):
        del self.sheets[name]
        return

    def load_dataframe(self, df, name=None, select=False):
        """Load a DataFrame into a new sheet
           Args:
            df: dataframe
            name: name of new sheet
            select: set new sheet as selected
        """

        if hasattr(self,'sheets'):
            self.add_sheet(sheetname=name, df=df, select=select)
        else:
            data = {name:{'table':df}}
            self.new_project(data)
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
        self.fileQuit()

    def sampleData(self, rows=None):
        if rows is None:
            rows, ok = QInputDialog.getInt(self, 'Rows', 'Rows:', 100)
        else:
            ok=True
        if ok:
            df = util.getSampleData(rows,5)
            self.add_sheet(None,df)
        return

    def get_current_table(self):

        idx = self.main.currentIndex()
        table = self.sheets[idx]#.table
        return table

    def zoomIn(self):

        w = self.get_current_table()
        w.table.zoomIn()
        return

    def zoomOut(self):

        w = self.get_current_table()
        w.table.zoomOut()
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

        text='DataExplore2 Application\n'\
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
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="msgpack",
                        help="Open a dataframe as msgpack", metavar="FILE")
    parser.add_option("-p", "--project", dest="projfile",
                        help="Open a dataexplore project file", metavar="FILE")
    parser.add_option("-i", "--csv", dest="csv",
                        help="Import a csv file", metavar="FILE")
    parser.add_option("-x", "--excel", dest="excel",
                        help="Import an excel file", metavar="FILE")
    parser.add_option("-t", "--test", dest="test",  action="store_true",
                        default=False, help="Run a basic test app")

    opts, remainder = parser.parse_args()

    app = QApplication(sys.argv)
    aw = Application()
    aw.show()
    app.exec_()
    #if opts.csv != None:
    #    t = app.import_file()

if __name__ == '__main__':
    main()

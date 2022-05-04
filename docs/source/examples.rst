Code Example
============

This section is for python programmers you want to use the table widget in their own programs.

Basics
------
Code::

	python
	from PySide2 import QtCore
	from PySide2.QtWidgets import *
	from PySide2.QtGui import *
	import pandas as pd
	from tablexplore import data, core, plotting, interpreter

	class TestApp(QMainWindow):
	    def __init__(self, project_file=None, csv_file=None):

	        QMainWindow.__init__(self)
	        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
	        self.setWindowTitle("Example")
	        self.setGeometry(QtCore.QRect(200, 200, 800, 600))
	        self.main = QWidget()
	        self.setCentralWidget(self.main)
	        layout = QVBoxLayout(self.main)
	        df = data.getSampleData()
	        t = core.DataFrameWidget(self.main,dataframe=df)
	        layout.addWidget(t)
	        #show a Python interpreter
	        t.showInterpreter()
	        return

	if __name__ == '__main__':
	    import sys
	    app = QApplication(sys.argv)
	    aw = TestApp()
	    aw.show()
	    app.exec_()

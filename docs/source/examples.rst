Code Examples
=============

This section is for Python programmers.

Basics
------

If you want to use the table widget in another GUI program::

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

Writing a plugin
----------------

This is quite straightforward if you are familiar with PyQt5/Pyside2. Built in plugins are kept in the plugin folder where the program is installed. You can look at these to get an idea how the plugins are written. When you make your own plugin, just add the .py file to the plugin folder under <home dir>/.config/tablexplore. It will be loaded when the program starts and added to the menu. You can add any code into the script, usually designed to execute using the table or plotter.  GUI based plugins will be added as docked widgets to the application.

Here is an example plugin::

	class ExamplePlugin(Plugin):
	    """Template plugin for TableExplore"""

	    #uncomment capabilities list to appear in menu
			capabilities = ['gui']
	    requires = ['']
	    menuentry = 'Example Plugin'
	    name = 'Example Plugin'

	    def __init__(self, parent=None, table=None):
	        """Customise this and/or doFrame for your widgets"""

	        if parent==None:
	            return
	        self.parent = parent
	        self.table = table
	        self.createWidgets()
	        return

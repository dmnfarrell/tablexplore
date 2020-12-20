<img align="right" src=tablexplore/logo.png width=150px>

# Tablexplore

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Tablexplore is an application for data analysis and plotting built in Python using the PySide2/Qt toolkit. It uses the pandas DataFrame class to store the table data. Pandas is an open source Python library providing high-performance data structures and data analysis tools.

## Installation

```
pip install -e git+https://github.com/dmnfarrell/tablexplore.git#egg=tablexplore
```

A Windows standalone binary will be available soon.

## Current features

* save and load projects
* import csv/hdf/from urls
* delete/add columns
* groupby-aggregate/pivot/transpose/melt operations
* merge tables
* show sub-tables
* python interpreter
* plotting mostly works

## Screenshots

<img src=docs/images/scr1.png width=600px>

## Use the widget in Python

```python
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
```

## See also

[pandastable - Tkinter based version](https://github.com/dmnfarrell/pandastable)

<img align="right" src=tablexplore/logo.png width=150px>

# Tablexplore

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Tablexplore is an application for data analysis and plotting built in Python using the PySide2/Qt toolkit. It uses the pandas DataFrame class to store the table data. Pandas is an open source Python library providing high-performance data structures and data analysis tools.

This application is intended primarily for educational/scientific use and allows quick visualization of data with convenient plotting. The primary goal is to let users explore their tables interactively without any prior programming knowledge and make interesting plots as they do this. One advantage is the ability to load and work with relatively large tables as compared to spreadsheets. The focus is on data manipulation rather than data entry. Though basic cell editing and row/column changes are supported.

## Installation

For all operating systems with Python and pip installed:

```
pip install -e git+https://github.com/dmnfarrell/tablexplore.git#egg=tablexplore
```

### Linux

The pip method above should work fine for most distributions but if you prefer you can also try the AppImage (experimental). Download from the latest [release page](https://github.com/dmnfarrell/tablexplore/releases) and run as follows:

```
chmod +x tablexplore-0.3.0-x86_64.AppImage
./tablexplore-0.3.0-x86_64.AppImage
```

There is also a [snap](https://snapcraft.io/tablexplore) available, which can be installed using:

```
snap install tablexplore
```

### Windows

A Windows standalone binary can be downloaded [here](https://dmnfarrell.github.io/tablexplore/).

## Current features

* save and load projects
* import csv/hdf/from urls
* delete/add columns
* groupby-aggregate/pivot/transpose/melt operations
* merge tables
* show sub-tables
* plotting mostly works
* apply column functions, resample, transform, string methods and date/time conversion
* python interpreter

## Screenshots

<img src=img/scr1.png width=600px>

## Usage

See [documentation](https://tablexplore.readthedocs.io/en/latest/)

## Videos

* [Introduction](https://youtu.be/0_KGjrNWpb4 )
* [Summarizing Data](https://youtu.be/acOzks3AKUQ)
* [Plotting](https://www.youtube.com/watch?v=ESCyyAERJ80)
* [Table Filtering](https://www.youtube.com/watch?v=aZjELBprGkA)
* [Joining tables](https://youtu.be/TDw4iS2u9Kg)

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

* [Homepage](https://dmnfarrell.github.io/tablexplore/)
* [documentation](https://tablexplore.readthedocs.io/en/latest/)
* [pandastable - Tkinter based version](https://github.com/dmnfarrell/pandastable)

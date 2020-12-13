#!/usr/bin/env python

"""    
    TablExplore app
    Created November 2020
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

from PySide2.QtWidgets import *
from tablexplore import app

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
    qapp = QApplication(sys.argv)
    aw = app.Application()
    aw.show()
    qapp.exec_()

if __name__ == '__main__':
    main()

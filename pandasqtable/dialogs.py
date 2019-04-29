#!/usr/bin/env python
"""
    Implements some dialog utilities for pandasqtable
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
import os, types
import string, copy
from collections import OrderedDict
try:
    import configparser
except:
    import ConfigParser as configparser
from PySide2 import QtCore, QtGui
from PySide2.QtCore import QObject
from PySide2.QtWidgets import *
from PySide2.QtGui import *

def dialogFromOptions(parent, opts, sections=None,
                      sticky='news',  layout='horizontal'):

    if sections == None:
        sections = {'options': opts.keys()}

    dialog = QWidget(parent)
    l = QHBoxLayout(dialog)
    for s in sections:
        f = QWidget()
        f.resize(100,100)
        f.sizeHint()
        l.addWidget(f)
        vb = QVBoxLayout(f)
        vb.setSpacing(2)
        for o in sections[s]:
            label = o
            opt = opts[o]
            if label in opt:
                label = opt['label']
            t = opt['type']
            vb.addWidget(QLabel(label))
            if t == 'combobox':
                w = QComboBox()
                w.addItems(opt['items'])
            elif t == 'entry':
                w = QLineEdit()
            elif t == 'slider':
                w = QSlider(QtCore.Qt.Horizontal)
                s,e = opt['range']
                w.setTickInterval(opt['interval'])
                w.setSingleStep((s-e)/10)
                w.setMinimum(s)
                w.setMaximum(e)
                w.setTickPosition(QSlider.TicksBelow)
            elif t == 'spinbox':
                w = QSpinBox()
            elif t == 'checkbutton':
                w = QCheckBox()
            elif t == 'font':
                w = QFontComboBox()
            vb.addWidget(w)

    return dialog

#!/usr/bin/env python
"""
    Some sample data sources for tablexplore classes.
    Created August 2020
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
import numpy as np
import pandas as pd

def getEmptyData(rows=10,columns=4):
    colnames = list(string.ascii_lowercase[:columns])
    df = pd.DataFrame(index=range(rows),columns=colnames)
    return df

def getSampleData(rows=400, cols=5):
    """Generate sample data"""

    colnames = list(string.ascii_lowercase[:cols])
    coldata = [np.random.normal(x,1,rows) for x in np.random.normal(5,3,cols)]
    n = np.array(coldata).T
    df = pd.DataFrame(n, columns=colnames)
    df['b'] = df.a*np.random.normal(.8, 0.1, len(df))
    df = np.round(df, 3)
    cats = ['green','blue','red','orange','yellow']
    df['label'] = [cats[i] for i in np.random.randint(0,5,rows)]
    #df['date'] = pd.date_range('1/1/2014', periods=rows, freq='H')
    return df

def getPresetData(name):
    """Get iris dataset"""

    path = os.path.dirname(__file__)
    df = pd.read_csv(os.path.join(path,'datasets','%s.csv' %name),index_col=0)
    return df

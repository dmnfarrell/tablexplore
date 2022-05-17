#!/usr/bin/env python
"""
    Implements the utility methods for tableexplore classes.
    Created August 2015
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
import random
import string, copy
import numpy as np
import pandas as pd
import matplotlib
import pylab as plt
import matplotlib.colors as colors

def valueToBool(value):
    return value.lower() == 'true' if isinstance(value, str) else bool(value)

def getEmptyData(rows=10,columns=4):

    colnames = list(string.ascii_lowercase[:columns])
    df = pd.DataFrame(index=range(rows),columns=colnames)
    return df

def gen_lower(n=2):
    """Generate lower case words"""
    return ''.join(random.choice(string.ascii_lowercase) for i in range(n))

def gen_upper(n=2):
    """Generate upper case words"""
    return ''.join(random.choice(string.ascii_uppercase) for i in range(n))

def gen_word(n=2):
    """Generate words with strings or symbols"""
    return ''.join(random.choice(string.printable) for i in range(n))

def getSampleData(rows=400, cols=5, namelen=2):
    """Generate sample data"""

    if namelen == 1:
        colnames = list(string.ascii_lowercase[:cols])
    else:
        colnames = [gen_lower(namelen) for i in range(cols)]
    if namelen==1 and cols>26:
        cols=26
    coldata = [np.random.normal(x,1,rows) for x in np.random.normal(5,3,cols)]
    n = np.array(coldata).T
    df = pd.DataFrame(n, columns=colnames)
    l0=df.columns[0]
    l1 = df.columns[1]
    df[l1] = df[l0]*np.random.normal(.8, 0.1, len(df))
    df = np.round(df, 3)
    cats = ['green','blue','red','orange','yellow']
    df['label'] = [cats[i] for i in np.random.randint(0,5,rows)]
    return df

def getPresetData(name):
    """Get iris dataset"""

    path = os.path.dirname(__file__)
    df = pd.read_csv(os.path.join(path,'datasets','%s.csv' %name),index_col=0)
    return df

def check_multiindex(index):
    """Check if index is a multiindex"""

    if isinstance(index, pd.MultiIndex):
        return 1
    else:
        return 0

def getAttributes(obj):
    """Get non hidden and built-in type object attributes that can be persisted"""

    d={}
    allowed = [str,int,float,list,tuple,bool,matplotlib.figure.Figure]
    for key in obj.__dict__:
        if key.startswith('_'):
            continue
        item = obj.__dict__[key]
        if type(item) in allowed:
            d[key] = item
        elif type(item) is dict:
            if checkDict(item) == 1:
                d[key] = item
    return d

def setAttributes(obj, data):
    """Set attributes from a dict. Used for restoring settings in tables"""

    for key in data:
        try:
            obj.__dict__[key] = data[key]
        except Exception as e:
            print (e)
    return

def checkDict(d):
    """Check a dict recursively for non serializable types"""

    allowed = [str,int,float,list,tuple,bool]
    for k, v in d.items():
        if isinstance(v, dict):
            checkDict(v)
        else:
            if type(v) not in allowed:
                return 0
    return 1

def getFonts():
     """Get the current list of system fonts"""

     import matplotlib.font_manager
     #l = matplotlib.font_manager.get_fontconfig_fonts()
     l = matplotlib.font_manager.findSystemFonts()
     fonts = []
     for fname in l:
        try: fonts.append(matplotlib.font_manager.FontProperties(fname=fname).get_name())
        except RuntimeError: pass
     fonts = list(set(fonts))
     fonts.sort()
     #f = matplotlib.font_manager.FontProperties(family='monospace')
     #print (matplotlib.font_manager.findfont(f))
     return fonts

def adjustColorMap(cmap, minval=0.0, maxval=1.0, n=100):
    """Adjust colormap to avoid using white in plots"""

    from matplotlib import colors
    new_cmap = colors.LinearSegmentedColormap.from_list(
        'trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=minval, b=maxval),
        cmap(np.linspace(minval, maxval, n)))
    return new_cmap

def colorScale(hex_color, brightness_offset=1):
    """Takes a hex color and produces a lighter or darker variant.
    Returns:
        new color in hex format
    """

    #if not hex_color.startswith('#'):
        #import matplotlib
        #hex_color = matplotlib.colors.cnames[hex_color].lower()
    if len(hex_color) != 7:
        raise Exception("Passed %s into color_variant(), needs to be in #87c95f format." % hex_color)
    rgb_hex = [hex_color[x:x+2] for x in [1, 3, 5]]
    new_rgb_int = [max(0, int(hex_value, 16) + brightness_offset) for hex_value in rgb_hex]
    r,g,b = [min([255, max([1, i])]) for i in new_rgb_int]
    # hex() produces "0x88", we want just "88"
    return "#{0:02x}{1:02x}{2:02x}".format(r, g, b)

def random_colors(n=10, seed=1):
    """Generate random hex colors as list of length n."""

    import random
    random.seed(seed)
    clrs=[]
    for i in range(n):
        r = lambda: random.randint(0,255)
        c='#%02X%02X%02X' % (r(),r(),r())
        clrs.append(c)
    return clrs

def gen_colors(cmap,n,reverse=False):
    '''Generates n distinct color from a given colormap.
    Args:
        cmap(str): The name of the colormap you want to use.
            Refer https://matplotlib.org/stable/tutorials/colors/colormaps.html to choose
            Suggestions:
            For Metallicity in Astrophysics: Use coolwarm, bwr, seismic in reverse
            For distinct objects: Use gnuplot, brg, jet,turbo.
        n(int): Number of colors you want from the cmap you entered.
        reverse(bool): False by default. Set it to True if you want the cmap result to be reversed.
    Returns:
        colorlist(list): A list with hex values of colors.
    Taken from the mycolorpy package by binodbhttr
    see also https://matplotlib.org/stable/tutorials/colors/colormaps.html
    '''

    c_map = plt.cm.get_cmap(str(cmap)) # select the desired cmap
    arr=np.linspace(0,1,n) #create a list with numbers from 0 to 1 with n items
    colorlist=list()
    for c in arr:
        rgba=c_map(c) #select the rgba value of the cmap at point c which is a number between 0 to 1
        clr=colors.rgb2hex(rgba) #convert to hex
        colorlist.append(str(clr)) # create a list of these colors

    if reverse==True:
        colorlist.reverse()
    return colorlist

def show_colors(colors, ax=None):
    """display a list of colors"""

    if ax == None:
        f,ax = plt.subplots(1,1,figsize=(6,1))
    ax.bar(range(len(colors)),height=1,color=colors,width=1)
    ax.axis('off')
    return

def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def checkOS():
    """Check the OS we are in"""

    from sys import platform as _platform
    if _platform == "linux" or _platform == "linux2":
        return 'linux'
    elif _platform == "darwin":
        return 'darwin'
    if "win" in _platform:
        return 'windows'

def get_user_config_directory():
    """Returns a platform-specific root directory for user config settings."""

    if os.name == "nt":
        appdata = os.getenv("LOCALAPPDATA")
        if appdata:
            return appdata
        appdata = os.getenv("APPDATA")
        if appdata:
            return appdata
        return None

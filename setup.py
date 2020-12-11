from setuptools import setup
import sys,os
home=os.path.expanduser('~')

with open('description.txt') as f:
    long_description = f.read()

setup(
    name = 'tablexplore',
    version = '0.1.0',
    description = 'Library for Qt tables using pandas DataFrames',
    long_description = long_description,
    url='https://github.com/dmnfarrell/tablexplore',
    license='GPL v3',
    author = 'Damien Farrell',
    author_email = 'farrell.damien@gmail.com',
    packages = ['tablexplore'],
    package_data={'tablexplore': ['../logo.png', '../description.txt',
                                  'styles/*.css','icons/*.png',
                                  'datasets/*.csv']},
    install_requires=['matplotlib>=3.0',
                      'pandas>=1.1',
                      'PySide2',
                      'xlrd>=1.0'],
    entry_points = { 'gui_scripts': [
                     'tablexplore = tablexplore.app:main']},
    classifiers = ['Operating System :: OS Independent',
            'Programming Language :: Python :: 3',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX',
            'Topic :: Software Development :: User Interfaces',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Development Status :: 4 - Beta',
            'Intended Audience :: Science/Research'],
    keywords = ['spreadsheet', 'table', 'pandas', 'data analysis', 'qt'],
)

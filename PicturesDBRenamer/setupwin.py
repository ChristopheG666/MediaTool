from distutils.core import setup
import py2exe
import sys

sys.path.append('../Lib')

#setup(console=['PicturesDBRenamer.py'])
setup(windows=['PicturesDBRenamer.pyw'])


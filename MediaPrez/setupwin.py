from distutils.core import setup
import py2exe
import sys

sys.path.append('../Lib')

#setup(console=['mediaprez.py'])
setup(windows=['mediaprez.pyw'])


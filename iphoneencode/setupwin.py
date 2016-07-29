from distutils.core import setup
import py2exe
import sys

sys.path.append('../Lib')

#setup(console=['iphoneencode.py'])
setup(windows=['iphoneencode.pyw'])
#      options={ "py2exe":{
#                        "unbuffered": True,
#                        "optimize": 2,
#                        "includes": ["GUIElement"]
#                } })


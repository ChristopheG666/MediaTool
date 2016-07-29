import os
import sys
import threading

if sys.version_info > (3, 0):
	from tkinter import *
else:
	from Tkinter import *

from PicturesDirManager import PicturesDirManager

sys.path.append('../Lib')
import GUIElement


EXT4DATE=[".JPG"]
EXT2MOVE=[".CR2", ".NEF"]
INIFILE=os.path.basename(sys.argv[0])+".ini"

class Gui(Tk,GUIElement.BasicList):
	def __init__(self, picturesDirManager):
		Tk.__init__(self)
		GUIElement.BasicList.__init__(self)
		self.msglock=threading.Lock()
		self.logmsg=[]

		self.picturesDirManager=picturesDirManager
		
		self.wm_title("Pictures DB Renamer")
		self.geometry('800x600')
		self.config(padx=3,pady=3)

		self.createListUI(self,"Directory","Rename directory",{'secondcolumn':True,'addbutton': False,'removebutton': False,'optionbutton': False, 'secondcolumnweight': 1},"New directory names")

		self.after(30,self.sendlog)

	def log(self,msg,popup=False):
		with self.msglock:
			self.logmsg.append([msg,popup])

	def sendlog(self):
		with self.msglock:
			for m in self.logmsg:
				self.addlog(m[0],m[1])
			self.logmsg=[]
		self.after(30,self.sendlog)

	def addelt(self,elt,elt2,highlight=True):
		GUIElement.BasicList.addelt(self,elt,elt2)
		if highlight:
			self.elt2list.itemconfigure(END,bg='green')

	def actionbtn(self):
		picturesDirManager.renameDir()

	def quitbtn(self):
		self.quit()

if len(sys.argv) == 2:
	rootdir=sys.argv[1]

else:
	rootdir="/Volumes/USBTOF2/Pictures/ToSort/"
	#rootdir=os.getcwd()


picturesDirManager=PicturesDirManager(rootdir,EXT4DATE,EXT2MOVE,INIFILE)
picturesDirManager.start()

gui = Gui(picturesDirManager)
picturesDirManager.gui=gui

gui.mainloop()

#rep=raw_input("Is it Ok (y/N)?")
#if rep.upper() == "Y":
#	imageDirManager.renameDir()

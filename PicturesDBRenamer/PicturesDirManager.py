import os
import shutil
import time
import threading

from PIL import Image
from PIL.ExifTags import TAGS


class PicturesDirManager(threading.Thread):
	def __init__(self,rootdir,EXT4DATE,EXT2MOVE,INIFILE):
		threading.Thread.__init__(self)
		self.gui=None

		self.rootdir=os.path.abspath(rootdir)
		self.EXT4DATE=EXT4DATE
		self.EXT2MOVE=EXT2MOVE
		self.EXT=EXT4DATE+EXT2MOVE
		self.dirlist=[]
		self.VERBOSE=9
		self.INIFILE=self.rootdir+os.sep+INIFILE
		self.dirlistdone=[]

	def run(self):
		#self.log("wait for UI",9)
		while self.gui == None:
			threading.Event().wait(0.01)

		self.log("in thread",9)

		self.loadINI()
		self.processWorktree()

	def __str__(self):
		ret=""
		for d in self.dirlist:
			ret=ret+str(d)+"\n"
		return ret

	def log(self,msg,level=1,popup=False):
		if self.VERBOSE>=level:
			if self.gui != None:
				self.gui.log(msg,popup)
			else:
				print(msg)

	def loadINI(self):
		try:
			ini=open(self.INIFILE,"r")
			for l in ini:
				self.dirlistdone.append(l.replace("\n",""))
			ini.close()
		except:
			self.log(".ini file "+self.INIFILE+" is not available")
		self.log("Directory already done:\n"+str(self.dirlistdone),9)


	def readImgExif(self, filename):
		ret = {}
    		i = Image.open(filename)
    		info = i._getexif()
    		for tag, value in info.items():
	        	decoded = TAGS.get(tag, tag)
	        	ret[decoded] = value
    		return ret

	def processWorktree(self):
		self.log("Starting in "+self.rootdir,0)
		dirList=os.listdir(self.rootdir)
		for dname in dirList:
			path=self.rootdir+os.sep+dname
			self.log("Find item "+path,9)
			if os.path.isdir(path):
				if dname in self.dirlistdone:
					self.log(dname+" already done",8)
					path=""
					newloc=""
					newlabel="Already done"
					labeltolog=""
				else:
					self.log("Find dir "+path)
					fileList=os.listdir(path)
					minDateTime=time.struct_time([3000,1,1,0,0,0,0,0,0])
					maxDateTime=time.struct_time([1000,1,1,0,0,0,0,0,0])
					findimg=False
					for fname in fileList:
						subpath=path+os.sep+fname
						self.log("Find item "+subpath,9)
						ext=os.path.splitext(subpath)[1].upper()
						if not os.path.isdir(subpath) and ext in self.EXT:
							findimg=True
							self.log("Find file "+subpath)
							if ext in self.EXT4DATE:
								try:
									exif=self.readImgExif(subpath)
									self.log("Image date "+exif['DateTime'], 9)
									datetime=time.strptime(exif['DateTime'],"%Y:%m:%d %H:%M:%S")
									if datetime > maxDateTime:
										maxDateTime=datetime
									if datetime < minDateTime:
										minDateTime=datetime
								except Exception as e:
									self.log("Error reading image info :"+str(e))
							else:
								dest=path+os.sep+ext[1:]
								if not os.path.exists(dest):
									self.log("Create dir "+dest,9)
									os.mkdir(dest)
								self.log("Moving file "+fname)
								os.rename(subpath,dest+os.sep+fname)		
					if findimg:
						self.log("Diff max-min date "+str((time.localtime(time.mktime(maxDateTime)-time.mktime(minDateTime))).tm_mday-1)+" days",9)
						if time.localtime(time.mktime(maxDateTime)-time.mktime(minDateTime)).tm_mday ==1:
							#min and max same day, the label is simpler
							newlabel=time.strftime("%Y_%m_%d",minDateTime)
						else:
							newlabel=time.strftime("%Y_%m_%d",maxDateTime)+"-"+time.strftime("%Y_%m_%d",minDateTime)
						if dname[0:len(newlabel)] == newlabel:
							#the directory already have the good label
							self.log(dname+" has already been renamed",9)
							newlabel=dname
							newloc=""
							labeltolog=dname
						else:
							newlabel=newlabel+" "+dname
							newloc=self.rootdir+os.sep+newlabel
							labeltolog=newlabel
						self.log("New dir name "+newloc)
					else:
						newlabel="No image found"
						newloc=""
						labeltolog=dname
						self.log(newlabel)
				self.dirlist.append({'dirlocation': path, 'dirlabel': dname, 'newlocation': newloc, 'newlabel': newlabel, 'labeltolog': labeltolog })
				self.gui.addelt(dname,newlabel,(newloc!=""))
	
	def renameDir(self):
		try:
			ini=open(self.INIFILE,"a")	
			for d in self.dirlist:
				if d['newlocation'] != "":
					self.log("Renaming "+d['dirlocation']+" to "+d['newlocation'])
					os.rename(d['dirlocation'],d['newlocation'])
				else:
					self.log("Nothing to do for "+d['dirlabel'],8)
				if d['labeltolog'] != "":
					ini.write(d['labeltolog']+"\n")
		except Exception, e:
			self.log("Error renaming directory\n"+str(e),popup=True)



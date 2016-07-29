import sys

if sys.version_info > (3, 0):
    from tkinter import *
else:
    from Tkinter import *

import threading
from threading import Thread, Lock, Event, local, currentThread
import re
import time
import shutil
import os
import traceback

sys.path.append('../Lib')
import GUIElement
import OSTools
import ShowDBUI
import Dnd
import time

gui = None


class ProcessThread(Thread):
    def __init__(self, file="", fileinfo=""):
        self.progress = -1
        self.globalprogress_start = -1
        self.globalprogress_end = -1
        self.progressmsg = ""
        self.askIDtoUserstr = ""
        self.askIDtoUserIDs = ""
        self.userID = ""
        self.log = ""
        self.displaymsg = ""
        self.timestart = 0
        self.timeeta = 0

        self.file = file
        self.fileinfo = fileinfo

        self.lock = Lock()
        self.eventmsg = Event()

        Thread.__init__(self)

    def run(self):
        try:
            log("process " + self.file + " in thread " + self.getName() + "\n")
            self.timestart = time.time()
            gui.processfilecbk(self.file, self.fileinfo)
            gui.processengine.threads.remove(self)
        except Exception, e:
            msg = "Global exception " + unicode(e) + "\n\n" + traceback.format_exc();
            print(msg)
            self.addlog(msg, True)
            os._exit(1)

    def updateglobalprogress(self, start, end):
        self.globalprogress_start = start
        self.globalprogress_end = end

    def updateprogress(self, subprogress, msg):
        # log(str(subprogress))
        with self.lock:
            try:
                subprogressf = float(subprogress)
            except:
                subprogressf = 0
            if self.globalprogress_start == -1 or self.globalprogress_end == -1:
                progress = subprogressf
            else:
                progress = self.globalprogress_start + (self.globalprogress_end - self.globalprogress_start) * float(
                    subprogressf) / 100.0
            new = (self.progress != progress)
            self.progress = progress
            curtime = time.time()
            if new or self.timeeta == 0:
                try:
                    self.timeeta = 100.0 * (curtime - self.timestart) / float(progress) + self.timestart
                except:
                    self.timeeta = 0
            if self.timeeta == 0:
                eta = "#"
                diff = "#"
                remain = "#"
            else:
                eta = time.strftime("%H:%M:%S", time.localtime(self.timeeta))
                diff = "%dh%02dm%02ds" % reduce(lambda ll, b: divmod(ll[0], b) + ll[1:],
                                                [((self.timeeta - self.timestart),), 60, 60])
                remain = "%dh%02dm%02ds" % reduce(lambda ll, b: divmod(ll[0], b) + ll[1:],
                                                  [((self.timeeta - curtime),), 60, 60])
            etamsg = "ETA " + eta + " (" + remain + "/" + diff + ")"
            if msg != "":
                self.progressmsg = msg + " file " + self.file + " " + etamsg
            else:
                self.progressmsg = etamsg
            # log("sub "+str(subprogress)+" prog "+str(progress)+" s "+str(self.globalprogress_start)+" e "+str(self.globalprogress_end))

    def addlog(self, logstr, displaymsg):
        with self.lock:
            self.log = self.log + unicode(self.getName()) + ": " + logstr + "\n"
            if displaymsg:
                self.displaymsg = logstr

        if displaymsg:
            self.eventmsg.clear()
            self.eventmsg.wait()

    def releaseEvent(self):
        self.eventmsg.set()

    def askIDtoUser(self, IDs):
        with self.lock:
            self.askIDtoUserstr = self.file
            self.askIDtoUserIDs = IDs
            self.userID = -1

        return self

    #	def askIDtoUserDone(self):
    #		with self.lock:
    #			self.userID=self.IDdiag.rep.get()
    #		self.IDdiag.destroy()

    def getIDfromUser(self):
        if self.userID == -1:
            log("Waiting for user answer")
            gui.processengine.putthreadonhold(self)
            while self.userID == -1 and needToStop() != True:
                time.sleep(0.1)
            gui.processengine.reinsertthread(self)

        return self.userID


class ProcessEngine():
    def __init__(self, maxthread):
        self.threads = []
        self.fileparams = {}

        self.stopall = False
        self.maxthread = maxthread + 1
        self.threadonhold = 0

        t0 = ProcessThread()
        t0.setName(currentThread().getName())
        self.threads.append(t0)

    def isAlive(self):
        return len(self.threads) > 1

    def count(self):
        return len(self.threads)

    def addfileinfo(self, filename, fileparams):
        self.fileparams[filename] = fileparams

    def processfile(self, file):
        if len(self.threads) >= self.maxthread:
            return True

        # create a thread to process the file
        log("Create a new Thread\n")
        self.stopall = False
        t = ProcessThread(file, self.fileparams[file])
        self.threads.append(t)
        t.start()

    def findThread(self):
        cur = currentThread()
        found = None
        for t in self.threads:
            if t.getName() == cur.getName():
                found = t
                break
        return found

    def addlog(self, logstr, displaymsg):
        self.findThread().addlog(logstr, displaymsg)

    def getUIParam(self):
        temp = {}
        temp['progressmsg'] = []
        temp['progress'] = []
        temp['log'] = []
        temp['displaymsg'] = []
        temp['askIDtoUser'] = []
        temp['askIDtoUserIDs'] = []
        for t in self.threads:
            with t.lock:
                temp['progress'].append(t.progress)
                temp['progressmsg'].append(t.progressmsg)
                t.progressmsg = ""
                temp['log'].append(t.log)
                t.log = ""
                temp['displaymsg'].append((t.displaymsg, t))
                t.displaymsg = ""
                temp['askIDtoUser'].append((t.askIDtoUserstr, t.askIDtoUserIDs, t))
                t.askIDtoUserstr = ""
                t.askIDtoUserIDs = None
        return temp

    def askIDtoUser(self, IDs):
        return self.findThread().askIDtoUser(IDs)

    def putthreadonhold(self, t):
        if len(self.threads) + self.threadonhold < 2 * self.maxthread - 1:
            self.threads.remove(t)
            self.threadonhold = self.threadonhold + 1

    def reinsertthread(self, t):
        # readd the thread
        if self.threads.count(t) == 0:
            self.threads.append(t)
            self.threadonhold = self.threadonhold - 1

    def updateglobalprogress(self, start, end):
        self.findThread().updateglobalprogress(start, end)

    def updateprogress(self, progress, msg):
        self.findThread().updateprogress(progress, msg)

    def stopProcessing(self):
        self.stopall = True
        time.sleep(0.2)


class Gui(Tk, GUIElement.BasicList, ShowDBUI.ShowDBUI):
    def __init__(self, title, nbthread, devicelabels, showDB):
        Tk.__init__(self)
        GUIElement.BasicList.__init__(self)
        ShowDBUI.ShowDBUI.__init__(self, showDB)

        # Process Engine class
        self.processengine = ProcessEngine(nbthread)

        nbthread = nbthread
        self.devicelabels = devicelabels

        self.wm_title(title)
        self.geometry('800x600')
        self.config(padx=3, pady=3)

        # Drag & Drop stuff
        self.pathstoadd = None
        self.dnd = Dnd.Dropable(self, self.dropFilesCbk)

        self.showprefs = IntVar()

        # ui
        self.createListUI(self, "File list queue", "")

        # Progress window
        self.progresswindow = Toplevel(self, padx=10, pady=10)
        self.progresswindow.protocol("WM_DELETE_WINDOW", "pass")
        self.progresswindow.wm_attributes("-topmost", 1)
        self.progresswindow.withdraw()
        Label(self.progresswindow, text="Progress...").pack()
        self.progressmsgfile = StringVar()
        Label(self.progresswindow, textvariable=self.progressmsgfile).pack()
        self.progressmsg = {}
        self.progressmsgwi = {}
        self.progress = {}
        for i in range(nbthread * 2 + 1):
            self.progress[i] = GUIElement.Meter(self.progresswindow, relief='ridge', bd=3)
            self.progressmsg[i] = StringVar()
            self.progressmsgwi[i] = Label(self.progresswindow, textvariable=self.progressmsg[i])
        Button(self.progresswindow, text="Cancel", command=lambda: self.processengine.stopProcessing()).pack()

    def createSpecialButton(self, frame, rowi):
        Checkbutton(frame, text="Review encoding param for each files", variable=self.showprefs).grid(row=rowi,
                                                                                                      column=0,
                                                                                                      sticky=W + E)

    # List callbacks
    def addbtn(self):
        self.addfile()
        return False

    def removebtn(self, elt):
        pass

    def updatebtn(self, elt):
        pass

    # newIDs=self.askIDtoUserDiag(elt,self.mediaPrez.getfileinfo(elt))
    # if newIDs.IDs[0] != "":
    #	self.mediaPrez.updatefileinfo(elt,newIDs)

    def optionbtn(self):
        self.openPrefs()

    def actionbtn(self):
        pass

    def quitbtn(self):
        self.quit()

    def openPrefs(self):
        guiparam = self.addfilegui(prefonly=True)
        if guiparam['returnval'].get():
            GP = self.getglobalparamcbk()
            GP['DEVICECONFS'] = guiparam['device'].get()
            if guiparam['destchoice'].get() == 1:
                GP['DESTDIR'] = ""
                GP['FINALDIR'] = ""
            elif guiparam['destchoice'].get() == 2:
                GP['DESTDIR'] = guiparam['dest'].get()
                GP['FINALDIR'] = ""
            else:
                GP['DESTDIR'] = guiparam['dest'].get()
                GP['FINALDIR'] = guiparam['destfinal'].get()
            GP['TAGLAN'] = guiparam['taglan'].get()
            GP['SUBLAN'] = guiparam['sublan'].get()
            GP['MOVIESET'] = guiparam['movieset'].get()
            self.getglobalparamcbk(GP)

    def addfile(self, path=None):
        if path == None or self.showprefs.get() == 1:
            guiparam = self.addfilegui(path=path)
            Ok = guiparam['returnval'].get()
            path = guiparam['path'].get()
            deviceconfs = guiparam['device'].get()
            if guiparam['destchoice'].get() == 1:
                dest = ""
                destfinal = ""
            elif guiparam['destchoice'].get() == 2:
                dest = guiparam['dest'].get()
                destfinal = ""
            else:
                dest = guiparam['dest'].get()
                destfinal = guiparam['destfinal'].get()
            taglan = guiparam['taglan'].get()
            sublan = guiparam['sublan'].get()
            movieset = guiparam['movieset'].get()
        else:
            Ok = True
            GP = self.getglobalparamcbk()
            deviceconfs = GP['DEVICECONFS']
            dest = GP['DESTDIR']
            destfinal = GP['FINALDIR']
            taglan = GP['TAGLAN']
            sublan = GP['SUBLAN']
            movieset = GP['MOVIESET']

        if Ok:
            filename = path
            if filename != "":
                self.addelt(filename)
                fileparams = {}
                fileparams['deviceconfs'] = deviceconfs
                fileparams['dest'] = dest
                fileparams['destfinal'] = destfinal
                fileparams['taglan'] = taglan
                fileparams['sublan'] = sublan
                fileparams['movieset'] = movieset
                self.processengine.addfileinfo(filename, fileparams)
                self.processfile()
            return filename
        else:
            return ""

    def addfilegui(self, path=None, prefonly=False):
        guiparam = {}
        guiparam['path'] = StringVar()
        guiparam['device'] = IntVar()
        guiparam['destchoice'] = IntVar()
        guiparam['dest'] = StringVar()
        guiparam['destfinal'] = StringVar()
        guiparam['returnval'] = BooleanVar(False)
        guiparam['taglan'] = StringVar()
        guiparam['sublan'] = StringVar()
        guiparam['movieset'] = StringVar()

        GP = self.getglobalparamcbk()

        if path != None:
            guiparam['path'].set(path)

        guiparam['destchoice'].set(1)
        if GP['DESTDIR'] != "":
            guiparam['dest'].set(GP['DESTDIR'])
            if GP['FINALDIR'] != "":
                guiparam['destfinal'].set(GP['FINALDIR'])
                guiparam['destchoice'].set(3)
            else:
                guiparam['destchoice'].set(2)
        guiparam['device'].set(GP['DEVICECONFS'])
        guiparam['taglan'].set(GP['TAGLAN'])
        guiparam['sublan'].set(GP['SUBLAN'])
        guiparam['movieset'].set(GP['MOVIESET'])

        filep = Toplevel(self, padx=10, pady=10)
        filep.protocol("WM_DELETE_WINDOW", "pass")

        if not prefonly:
            f = Frame(filep, border=1, relief=SUNKEN, padx=2, pady=2)
            f.pack(anchor=W, fill=BOTH)
            f.grid_columnconfigure(0, weight=1)

            Label(f, text="Select the file to transcode:").grid(row=0, column=0)
            Entry(f, textvariable=guiparam['path']).grid(row=1, column=0, sticky=W + E)
            Button(f, text="Browse", command=lambda: OSTools.browse4filename(filep, "Open file to transcode", [
                ("Video files", ("*avi", "*.mkv", "*.mp4")), ("All files", "*.*")], guiparam['path'])).grid(row=1,
                                                                                                            column=1,
                                                                                                            sticky=W + E)

        Label(filep, text="Encoding paramaters").pack(anchor=W)
        f = Frame(filep, border=1, relief=SUNKEN, padx=2, pady=2)
        f.pack(anchor=W, fill=BOTH)
        Label(f, text="Select the device to transcode to:").pack(anchor=W)
        for i in range(len(self.devicelabels)):
            Radiobutton(f, text=self.devicelabels[i], variable=guiparam['device'], value=i).pack(anchor=W)
        f = Frame(filep, border=1, relief=SUNKEN, padx=2, pady=2)
        f.pack(anchor=W, fill=BOTH)
        f.grid_columnconfigure(1, weight=1)
        f.grid_columnconfigure(3, weight=1)
        Label(f, text="Select output dir (Please read the manual):").grid(row=0, column=0)
        Radiobutton(f, text="Same dir as source", variable=guiparam['destchoice'], value=1).grid(row=1, column=0,
                                                                                                 sticky=W)
        Radiobutton(f, text="To this dir", variable=guiparam['destchoice'], value=2).grid(row=2, column=0, sticky=W)
        Radiobutton(f, text="First to one dir and then to another", variable=guiparam['destchoice'], value=3).grid(
            row=3, column=0, sticky=W)
        Entry(f, textvariable=guiparam['dest']).grid(row=2, column=1, sticky=W + E)
        Entry(f, textvariable=guiparam['dest']).grid(row=3, column=1, sticky=W + E)
        Entry(f, textvariable=guiparam['destfinal']).grid(row=3, column=3, sticky=W + E)
        Button(f, text="Browse", command=lambda: OSTools.browse4dir(filep, "Select directory", guiparam['dest'])).grid(
            row=2, column=2, sticky=W + E)
        Button(f, text="Browse", command=lambda: OSTools.browse4dir(filep, "Select directory", guiparam['dest'])).grid(
            row=3, column=2, sticky=W + E)
        Button(f, text="Browse",
               command=lambda: OSTools.browse4dir(filep, "Select directory", guiparam['destfinal'])).grid(row=3,
                                                                                                          column=4,
                                                                                                          sticky=W + E)

        f = Frame(filep, border=1, relief=SUNKEN, padx=2, pady=2)
        f.pack(anchor=W, fill=BOTH)
        f.grid_columnconfigure(1, weight=1)
        f.grid_columnconfigure(3, weight=1)
        Label(f, text="Tag langugage ID (en for english, fr for french, etc...):").grid(row=0, column=0)
        Entry(f, textvariable=guiparam['taglan']).grid(row=0, column=1, sticky=W + E)

        f = Frame(filep, border=1, relief=SUNKEN, padx=2, pady=2)
        f.pack(anchor=W, fill=BOTH)
        f.grid_columnconfigure(1, weight=1)
        f.grid_columnconfigure(3, weight=1)

        Label(f, text="XBMC .nfo prefs").grid(row=1, column=0)
        Label(f,
              text="Subtitle download langugage ID (empty for no download, eng for english, fre for french, etc...):").grid(
            row=2, column=0)
        Entry(f, textvariable=guiparam['sublan']).grid(row=2, column=1, sticky=W + E)
        Label(f, text="Movie set (empty for None):").grid(row=3, column=0)
        Entry(f, textvariable=guiparam['movieset']).grid(row=3, column=1, sticky=W + E)

        f = Frame(filep, padx=2, pady=2)
        f.pack()
        Button(f, text="Go", command=lambda: guiparam['returnval'].set(True), width=20).grid(row=0, column=0, sticky=W)
        Button(f, text="Cancel", command=lambda: guiparam['returnval'].set(False), width=20).grid(row=0, column=1,
                                                                                                  sticky=E)

        self.wait_variable(guiparam['returnval'])
        filep.destroy()

        return guiparam

    def dropFilesCbk(self, paths):
        self.pathstoadd = paths
        pass

    def dropFilesWatch(self):
        if self.pathstoadd != None:
            paths = self.pathstoadd
            self.pathstoadd = None
            for path in paths:
                log("call add file " + path)
                self.addfile(path)
        self.after(30, self.dropFilesWatch)

    def mainloop(self):
        self.processfile()
        self.after(30, self.updateui)
        self.after(30, self.dropFilesWatch)
        Tk.mainloop(self)

    def quit(self):
        self.processengine.stopProcessing()
        if self.processengine.isAlive():
            self.after(30, self.quit)
            return

        self.cleanquitcbk()
        self.destroy()

    def processfile(self):
        if self.listsize() == 0:
            return

        self.updatestatus("Processing files")
        # open progress window
        if self.progresswindow.state() == 'withdrawn':
            self.progresswindow.deiconify()
            ng = '+%d+%d' % (self.winfo_rootx() + self.winfo_width() / 4, self.winfo_rooty() + self.winfo_height() / 4)
            self.progresswindow.geometry(ng)

        file = self.getnextelt(False)
        if not self.processengine.processfile(file):
            self.removenextelt()

    def updateui(self):
        filecount = self.listsize() + self.processengine.count() + self.processengine.threadonhold - 1

        if filecount == 0:
            self.progresswindow.withdraw()
            self.updatestatus("Done")
        else:
            self.progressmsgfile.set(unicode(
                self.processengine.count() + self.processengine.threadonhold - 1) + " files processed, " + unicode(
                self.listsize()) + " files left to process")

        UIParam = self.processengine.getUIParam()
        for i in range(self.processengine.count()):
            if i != 0:
                self.progressmsgwi[i].pack()
                self.progress[i].pack()

            try:
                self.progress[i].set(float(UIParam['progress'][i]) / 100.0)
            except:
                self.progress[i].set(0)
            if UIParam['progressmsg'][i] != "":
                self.progressmsg[i].set(UIParam['progressmsg'][i])

            if UIParam['log'][i] != "":
                self.addlog(UIParam['log'][i])

            if UIParam['displaymsg'][i][0] != "":
                self.addlog(UIParam['displaymsg'][i][0], True)
                UIParam['displaymsg'][i][1].releaseEvent()

            if UIParam['askIDtoUser'][i][0] != "":
                UIParam['askIDtoUser'][i][2].userID = self.askIDtoUserDiag(UIParam['askIDtoUser'][i][0],
                                                                           UIParam['askIDtoUser'][i][1])
            #	"Please give the movie/serie ID","Please give movie/serie ID for "+UIParam['askIDtoUser'][i][0]+"\n(On www.themoviedbi.org for movie and www.thetvdb.com for series)",UIParam['askIDtoUser'][i][1],UIParam['askIDtoUser'][i][2])

        for i in range(self.processengine.count(), 2 * self.processengine.maxthread - 1, 1):
            self.progress[i].set(0.0)
            self.progressmsgwi[i].pack_forget()
            self.progress[i].pack_forget()
            self.progressmsg[i].set("")

        self.processfile()

        self.after(30, self.updateui)


def launchGUI(title, nbthread, devicelabels, processfilecbk, cleanquitcbk, getglobalparamcbk, showDB):
    global gui

    gui = Gui(title, nbthread, devicelabels, showDB)

    gui.processfilecbk = processfilecbk
    gui.cleanquitcbk = cleanquitcbk
    gui.getglobalparamcbk = getglobalparamcbk

    GP = getglobalparamcbk()
    if GP['SHOWPREFS']:
        gui.showprefs.set(1)
    else:
        gui.showprefs.set(0)

    gui.mainloop()


def log(logstr, displaymsg=False):
    logstr = unicode(logstr)
    if gui is not None:
        gui.processengine.addlog(logstr, displaymsg)
    else:
        print(logstr)


def globalprogress(start, end):
    if gui is None:
        log("Global Progress", False)
    else:
        gui.processengine.updateglobalprogress(start, end)


def progress(progress=-1, msg=""):
    if gui is None:
        log("Progress " + unicode(progress) + "                                                          ", False)
    else:
        gui.processengine.updateprogress(progress, msg)


def needToStop():
    if gui is not None:
        return gui.processengine.stopall
    else:
        return False


def askIDtoUser(filename, IDs=None):
    if gui is None:
        log("Please give the ID for " + filename)
        return sys.stdin.readline()
    else:
        return gui.processengine.askIDtoUser(IDs)


def getIDfromUser(th):
    return th.getIDfromUser()


def filewithfeedback(src, dst, action, msg=""):
    actionthread = FileAction(src, dst, action)
    actionthread.start()

    status = os.stat(src)
    target = status.st_size
    val = -1.0
    while not actionthread.error and not actionthread.done:
        try:
            status = os.stat(dst)
            val = status.st_size
        except Exception, e:
            val = 0.0
        progress(val * 100.0 / target, msg)
        time.sleep(0.1)

    if actionthread.error:
        raise Exception(actionthread.errorstr)


class FileAction(Thread):
    def __init__(self, src, dst, action):
        self.src = src
        self.dst = dst
        self.action = action
        self.error = False
        self.done = False
        self.errorstr = ""
        Thread.__init__(self)

    def run(self):
        try:
            if self.action == "move":
                shutil.move(self.src, self.dst)
            else:
                shutil.copy(self.src, self.dst)
        except Exception, e:
            self.error = True
            self.errorstr = unicode(e)
        self.done = True

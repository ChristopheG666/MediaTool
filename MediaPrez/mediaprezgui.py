import sys

if sys.version_info > (3, 0):
    from tkinter import *
else:
    from Tkinter import *

import re
import time
import shutil
import os

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "Lib"))
from ShowDB import ShowIDs
import GUIElement
import ShowDBUI
import OSTools
import Dnd

gui = None


class Gui(Tk, GUIElement.BasicList, ShowDBUI.ShowDBUI):
    def __init__(self, title, mediaPrez, showDB):
        Tk.__init__(self)
        GUIElement.BasicList.__init__(self)
        ShowDBUI.ShowDBUI.__init__(self, showDB)

        self.mediaPrez = mediaPrez

        self.wm_title(title)
        self.geometry('800x600')
        self.config(padx=3, pady=3)

        self.recursdir = IntVar()

        # Drag & Drop stuff
        self.pathstoadd = None
        self.dnd = Dnd.Dropable(self, self.dropFilesCbk)

        # ui
        self.createListUI(self, "File list", "Generate output", {'secondcolumn': True}, "Subtitles")

    def createSpecialButton(self, frame, rowi):
        Button(frame, text="Add dir", command=self.adddirgui).grid(row=rowi, column=0, sticky=W + E)
        Checkbutton(frame, text="Recursive", variable=self.recursdir).grid(row=rowi, column=1, sticky=W + E)
        pass

    # List callbacks
    def addbtn(self):
        self.addfile(OSTools.browse4filename(self, "Open file to add",
                                             [("Video files", ("*avi", "*.mkv", "*.mp4")), ("All files", "*.*")]))
        return False

    def removebtn(self, elt):
        self.mediaPrez.removefile(elt)

    def updatebtn(self, elt):
        if elt == "":
            return
        GP = self.mediaPrez.GetGlobalParam()
        newIDs = self.askIDtoUserDiag(elt, self.mediaPrez.getfileinfo(elt), GP['SUBLAN'], GP['MOVIESET'],
                                      lambda filename, imdb: self.mediaPrez.downloadSubtitle(filename, imdb))
        if newIDs.IDs[0] != "":
            self.mediaPrez.updatefileinfo(elt, newIDs)

    def updatebtn2(self, elt, elt2):
        if elt == "":
            return
        GP = self.mediaPrez.GetGlobalParam()
        fp = self.mediaPrez.getfileinfo(elt)
        fp.imdb = self.getimdbsub(elt, [GP['DEFAULTSUBLAN1'], GP['DEFAULTSUBLAN2']])
        self.mediaPrez.downloadSubtitle(elt, fp.imdb, False)

    def optionbtn(self):
        self.openPrefs()

    def actionbtn(self):
        self.mediaPrez.generateoutput()

    def quitbtn(self):
        self.destroy()

    def addfile(self, filename):
        if os.path.isdir(filename):
            dirList = os.listdir(filename)
            for fname in dirList:
                path = os.path.join(filename, fname)
                if os.path.isdir(path):
                    if self.recursdir.get() == 1:
                        self.addfile(path)
                else:
                    if os.path.splitext(path)[1].lower() in self.moviefilter:
                        self.addfile(path)
            updatestatus("Done")
        else:
            if not self.processfile(filename):
                self.addelt(filename, self.mediaPrez.getfileallinfo(filename)['substatus'])
            else:
                self.updateelt2(filename, self.mediaPrez.getfileallinfo(filename)['substatus'])

    def adddirgui(self):
        self.addfile(OSTools.browse4dir(self, "Open dir to add"))

    def dropFilesCbk(self, paths):
        self.pathstoadd = paths

    def dropFilesWatch(self):
        if self.pathstoadd != None:
            paths = self.pathstoadd
            self.pathstoadd = None
            for path in paths:
                log("call add file " + path)
                self.addfile(path)
        self.after(30, self.dropFilesWatch)

    def openPrefs(self):
        guiparam = {}
        guiparam['destdir'] = StringVar()
        guiparam['localroot'] = StringVar()
        guiparam['remoteroot'] = StringVar()
        guiparam['taglan'] = StringVar()
        guiparam['sublan'] = StringVar()
        guiparam['movieset'] = StringVar()
        guiparam['force'] = IntVar()
        guiparam['remoterelat'] = IntVar()
        guiparam['moviefilter'] = StringVar()
        guiparam['returnval'] = BooleanVar(False)

        GP = self.mediaPrez.GetGlobalParam()

        guiparam['destdir'].set(GP['DESTDIR'])
        guiparam['localroot'].set(GP['LOCALROOT'])
        guiparam['remoteroot'].set(GP['REMOTEROOT'])
        guiparam['taglan'].set(GP['TAGLAN'])
        guiparam['sublan'].set(GP['SUBLAN'])
        guiparam['movieset'].set(GP['MOVIESET'])
        guiparam['force'].set(GP['FORCERELOAD'])
        guiparam['remoterelat'].set(GP['REMOTERELAT'])
        guiparam['moviefilter'].set(GP['MOVIEFILTER'])

        filep = Toplevel(self, padx=10, pady=10)
        filep.protocol("WM_DELETE_WINDOW", "pass")

        Label(filep, text="Options").pack(anchor=W)
        f = Frame(filep, border=1, relief=SUNKEN, padx=2, pady=2)
        f.pack(anchor=W, fill=BOTH, expand=1)
        # f.grid_columnconfigure(0,weight=1)
        f.grid_columnconfigure(1, weight=1)
        # f.grid_columnconfigure(2,weight=1)
        rowi = 0
        Label(f, text="Select output dir:").grid(row=rowi, column=0)
        Entry(f, textvariable=guiparam['destdir']).grid(row=rowi, column=1, sticky=W + E)
        Button(f, text="Browse",
               command=lambda: OSTools.browse4dir(filep, "Destination directory", guiparam['destdir'])).grid(row=rowi,
                                                                                                             column=2,
                                                                                                             sticky=W + E)
        rowi = rowi + 1
        Label(f, text="Local root dir:").grid(row=rowi, column=0)
        Entry(f, textvariable=guiparam['localroot']).grid(row=rowi, column=1, sticky=W + E)
        Button(f, text="Browse",
               command=lambda: OSTools.browse4dir(filep, "Local root directory", guiparam['localroot'])).grid(row=rowi,
                                                                                                              column=2,
                                                                                                              sticky=W + E)
        rowi = rowi + 1
        Label(f, text="Remote root dir:").grid(row=rowi, column=0)
        Entry(f, textvariable=guiparam['remoteroot']).grid(row=rowi, column=1, sticky=W + E)
        Button(f, text="Browse",
               command=lambda: OSTools.browse4dir(filep, "Remote root directory", guiparam['remoteroot'])).grid(
            row=rowi, column=2, sticky=W + E)
        rowi = rowi + 1
        Checkbutton(f, text="Remote dir is relative", variable=guiparam['remoterelat']).grid(row=rowi, column=0,
                                                                                             sticky=W + E)
        Button(f, text="Remote is PCH/Popcorn",
               command=lambda: guiparam['remoteroot'].set("file:///opt/sybhttpd/localhost.drives/HARD_DISK/")).grid(
            row=rowi, column=2, sticky=W + E)

        rowi = 0
        f = Frame(filep, border=1, relief=SUNKEN, padx=2, pady=2)
        f.pack(anchor=W, fill=BOTH, expand=1)
        # f.grid_columnconfigure(0,weight=1)
        f.grid_columnconfigure(1, weight=1)
        Label(f, text="Filter for videos file (.avi,.mkv ...):").grid(row=rowi, column=0)
        Entry(f, textvariable=guiparam['moviefilter']).grid(row=rowi, column=1, sticky=W + E)

        rowi = rowi + 1
        Label(f, text="Tag langugage ID (en for english, fr for french, etc...):").grid(row=rowi, column=0)
        Entry(f, textvariable=guiparam['taglan']).grid(row=rowi, column=1, sticky=W + E)
        rowi = rowi + 1
        Checkbutton(f, text="Force reload from the web", variable=guiparam['force']).grid(row=rowi, column=1,
                                                                                          sticky=W + E)
        f.pack(anchor=W, fill=BOTH, expand=1)

        rowi = 0
        f = Frame(filep, border=1, relief=SUNKEN, padx=2, pady=2)
        f.pack(anchor=W, fill=BOTH, expand=1)
        # f.grid_columnconfigure(0,weight=1)
        f.grid_columnconfigure(1, weight=1)
        Label(f, text="XBMC .nfo prefs:").grid(row=rowi, column=0)

        rowi = rowi + 1
        Label(f, text="Subtitles langugage ID (empty for none, fre for french, eng for english, etc...):").grid(
            row=rowi, column=0)
        Entry(f, textvariable=guiparam['sublan']).grid(row=rowi, column=1, sticky=W + E)
        rowi = rowi + 1
        Label(f, text="Movie set (empty for None):").grid(row=rowi, column=0)
        Entry(f, textvariable=guiparam['movieset']).grid(row=rowi, column=1, sticky=W + E)

        f.pack(anchor=W, fill=BOTH, expand=1)

        f = Frame(filep, padx=2, pady=2)
        f.pack()
        Button(f, text="Go", command=lambda: guiparam['returnval'].set(True), width=20).grid(row=0, column=0, sticky=W)
        Button(f, text="Cancel", command=lambda: guiparam['returnval'].set(False), width=20).grid(row=0, column=1,
                                                                                                  sticky=E)

        self.wait_variable(guiparam['returnval'])
        filep.destroy()

        if guiparam['returnval'].get():
            GP['DESTDIR'] = guiparam['destdir'].get()
            GP['LOCALROOT'] = guiparam['localroot'].get()
            GP['REMOTEROOT'] = guiparam['remoteroot'].get()
            GP['TAGLAN'] = guiparam['taglan'].get()
            GP['SUBLAN'] = guiparam['sublan'].get()
            GP['MOVIESET'] = guiparam['movieset'].get()
            GP['FORCERELOAD'] = guiparam['force'].get()
            GP['REMOTERELAT'] = guiparam['remoterelat'].get()
            GP['MOVIEFILTER'] = guiparam['moviefilter'].get()
            self.updateMovieFilter(GP['MOVIEFILTER'])
            self.mediaPrez.SetGlobalParam(GP)

    def updateMovieFilter(self, liststr):
        self.moviefilter = liststr.lower().split(",")

    def processfile(self, file):
        return self.mediaPrez.processfile(file)

    def mainloop(self):
        self.after(30, self.dropFilesWatch)
        Tk.mainloop(self)


def launchGUI(title, mediaPrez):
    global gui, debug

    gui = Gui(title, mediaPrez, mediaPrez.showDB)
    debug = mediaPrez.GetGlobalParam()['DEBUG']
    if mediaPrez.GetGlobalParam()['RECURSIVE']:
        gui.recursdir.set(1)
    else:
        gui.recursdir.set(0)
    gui.updateMovieFilter(mediaPrez.GetGlobalParam()['MOVIEFILTER'])
    gui.mainloop()


debug = False


def log(logstr, displaymsg=False, parentwindow=None):
    logstr = unicode(logstr)

    if gui is not None:
        gui.addlog(logstr, displaymsg, parentwindow)
        if debug:
            print(logstr)
    else:
        print(logstr)


def updatestatus(logstr, displaymsg=False):
    logstr = unicode(logstr)
    log(logstr, displaymsg)

    if gui is not None:
        gui.updatestatus(logstr)


def askIDtoUser(filename, IDs=None, sublan="", movieset=""):
    if gui is None:
        log("Please give the ID for " + filename)
        return sys.stdin.readline()
    else:
        return gui.askIDtoUserDiag(filename, IDs, sublan, movieset,
                                   lambda filename, imdb: gui.mediaPrez.downloadSubtitle(filename, imdb))


def updateelt2(filename, newelt2):
    if gui is None:
        return
    gui.updateelt2(filename, newelt2)

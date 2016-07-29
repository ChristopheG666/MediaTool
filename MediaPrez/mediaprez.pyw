#! /usr/bin/env python
import subprocess
import sys
import os
import shutil
import mediaprezgui
import distutils.dir_util
import traceback
import codecs

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "Lib"))
from ShowDB import ShowDB, ShowIDs

GLOBALPARAM = {}
GLOBALPARAM['version'] = "Alpha 2"

SPLITTAG = "<TAGFORPARSING>"
SPLITINDENT = "<TAGFORPARSINGINDENT>"

TRASHFILE = "tag.trash"

if sys.version_info > (3, 0):
    def execfile(filename):
        exec (compile(open(filename).read(), filename, 'exec'))

# import pdb; pdb.set_trace()

class Parser:
    def __init__(self, path):
        self.name = ""
        self.path = path
        self.content = []
        self.keys = []
        self.load()
        self.field = {}
        self.borderimg = None

    def load(self):
        try:
            f = codecs.open(self.path, "r", "utf-8")
            filec = ""
            for l in f:
                filec = filec + l
            f.close()
        except:
            mediaprezgui.log("Error reading file " + self.path)
        strident = filec.split(SPLITINDENT)
        for indent in strident:
            content = []
            keys = []
            strarr = indent.split(SPLITTAG)
            for i in range(0, len(strarr), 2):
                content.append(strarr[i])
                if i + 1 < len(strarr):
                    keys.append(strarr[i + 1])
            self.content.append(content)
            self.keys.append(keys)

    def initfield(self, filelist, prev, nex, index=0):
        pass

    def dump(self, filelist, prev=None, nex=None):
        self.initfield(filelist, prev, nex)
        self.createfile()

        for c in range(len(self.content)):
            content = self.content[c]
            keys = self.keys[c]
            if (c % 2) == 0:
                self.initfield(filelist, prev, nex)
                for i in range(len(content) - 1):
                    self.write(content[i])
                    self.write(self.field[keys[i]])
                self.write(content[len(content) - 1])
            else:
                for fi in range(len(filelist)):
                    self.initfield(filelist, prev, nex, fi)
                    for i in range(len(content) - 1):
                        self.write(unicode(content[i]))
                        self.write(unicode(self.field[keys[i]]))
                    self.write(content[len(content) - 1])
        self.closefile()

    def convertPath(self, localpath):
        newpath = localpath.replace(GLOBALPARAM['LOCALROOT'], GLOBALPARAM['REMOTEROOT']).replace("\\", "/").replace(
            "//", "/").replace("file://o", "file:///o")
        if not GLOBALPARAM['REMOTERELAT'] and newpath[0:7] != "file://":
            newpath = "file://" + newpath
        return newpath

    def createfile(self):
        path = os.path.join(GLOBALPARAM['DESTDIR'], "Media", self.name)
        mediaprezgui.log("Creating file " + path)
        self.output = codecs.open(path, "w", "utf-8")

    def write(self, line):
        self.output.write(line)

    def closefile(self):
        self.output.close()

    def copyfile(self, src, dst, resize=None):
        if os.path.exists(dst):
            return
        try:
            # if True:
            #import PIL
            import math
            #from PIL import Image

            try:
                # if True:
                if self.borderimg == None:
                    self.borderimg = {}
                    self.borderimg['Poster'] = {}
                    self.borderimg['Small'] = {}
                    img = Image.open(os.path.join(GLOBALPARAM['DESTDIR'], "Media", "bordermask.png"))
                    self.borderimg['Poster']['mask'] = img.split()[1]
                    self.borderimg['Small']['mask'] = \
                        img.resize((GLOBALPARAM['SMALL_W'], GLOBALPARAM['SMALL_H']), Image.ANTIALIAS).split()[1]
                    img = Image.open(os.path.join(GLOBALPARAM['DESTDIR'], "Media", "border.png"))
                    self.borderimg['Poster']['src'] = img
                    self.borderimg['Small']['src'] = img.resize((GLOBALPARAM['SMALL_W'], GLOBALPARAM['SMALL_H']),
                                                                Image.ANTIALIAS)

                img = Image.open(src)
                if resize == 'Small':
                    size = (GLOBALPARAM['SMALL_W'], GLOBALPARAM['SMALL_H'])
                elif resize == 'Poster':
                    size = (GLOBALPARAM['POSTER_W'], GLOBALPARAM['POSTER_H'])
                elif resize == 'Fanart':
                    size = (GLOBALPARAM['SCREEN_W'], GLOBALPARAM['SCREEN_H'])
                else:
                    resize = None
                if resize != 'None':
                    img = img.resize(size, Image.ANTIALIAS)
                if resize == 'Poster' or resize == 'Small':
                    img = img.convert('RGBA')
                    W = size[0]
                    H = size[1]
                    a = 0.03
                    A = 1 - 2 * a
                    D = -a * H / W
                    G = -2 * a / W
                    img = img.transform(size, Image.PERSPECTIVE, (A, 0, 0, D, 1, 0, G, 0), Image.BICUBIC)
                    temp = self.borderimg[resize]['src'].copy()
                    temp.paste(img, mask=self.borderimg[resize]['mask'])
                    img = temp

                img.save(dst, "PNG")
            except Exception as e:
                # else:
                mediaprezgui.log("Error genrating image file " + src + " to " + dst + "\n" + str(e))
        except Exception as e:  # the module PIl is not installed
            # else:
            try:
                shutil.copy(src, dst)
            except Exception as e:
                mediaprezgui.log("Error genrating image file " + src + " to " + dst + "\n" + str(e))


class IndexParser(Parser):
    def __init__(self, name, path):
        Parser.__init__(self, path)
        self.name = name

    def initfield(self, filelist, prev, nex, index=0):
        self.field = {}
        fileinfo = filelist[index]
        l = len(filelist)
        titlelist = ""
        for i in range(l):
            titlelist = titlelist + "\"" + filelist[i]['meta']['showname'] + "\""
            if i < l - 1:
                titlelist = titlelist + ",\n"
            else:
                titlelist = titlelist + "\n"
        self.field['TitleList'] = titlelist
        self.field['Filename'] = fileinfo['noext'] + ".html"
        self.field['Index'] = str(index + 1)
        self.field['Playlist'] = fileinfo['noext'] + ".playlist.jsp"
        self.field['Poster'] = fileinfo['noext'] + "Small.png"
        self.copyfile(fileinfo['DB']['IMGFILE'], os.path.join(GLOBALPARAM['DESTDIR'], "Media", self.field['Poster']),
                      'Small')
        if ((index + 1) % 7) == 0:
            self.field['ENDL'] = "</tr><tr>"
        else:
            self.field['ENDL'] = ""


class MovieParser(Parser):
    def initfield(self, filelist, prev, nex, index=0):
        self.name = filelist[0]['noext'] + ".html"
        fileinfo = filelist[0]
        fileinfo['DB']['MediaImg'] = fileinfo['noext'] + ".png"
        fileinfo['DB']['FanartImg'] = fileinfo['noext'] + "Fanart.jpg"
        self.copyfile(fileinfo['DB']['IMGFILE'],
                      os.path.join(GLOBALPARAM['DESTDIR'], "Media", fileinfo['DB']['MediaImg']),
                      'Poster')
        self.copyfile(fileinfo['DB']['FANFILE'],
                      os.path.join(GLOBALPARAM['DESTDIR'], "Media", fileinfo['DB']['FanartImg']),
                      'Fanart')
        self.field = {}
        self.field['Title'] = fileinfo['meta']['showname']
        self.field['Fanart'] = fileinfo['DB']['FanartImg']
        self.field['Poster'] = fileinfo['DB']['MediaImg']
        self.field['Left'] = prev['noext'] + ".html"
        self.field['Right'] = nex['noext'] + ".html"
        self.field['Prev'] = prev['noext'] + ".html"
        self.field['Next'] = nex['noext'] + ".html"
        self.field['Filename'] = self.convertPath(fileinfo['filename'])
        self.field['Year'] = fileinfo['meta']['released']
        self.field['Duration'] = ""
        self.field['Overview'] = fileinfo['meta']['overview']


class SerieParser(Parser):
    def initfield(self, filelist, prev, nex, index=0):
        self.name = filelist[0]['noext'] + ".html"
        self.field = {}
        fileinfo = filelist[index]
        if index == 0:
            fileinfo['DB']['MediaImg'] = fileinfo['noext'] + ".png"
            fileinfo['DB']['FanartImg'] = fileinfo['noext'] + "Fanart.jpg"
            self.copyfile(fileinfo['DB']['IMGFILE'],
                          os.path.join(GLOBALPARAM['DESTDIR'], "Media", fileinfo['DB']['MediaImg']),
                          'Poster')
            self.copyfile(fileinfo['DB']['FANFILE'],
                          os.path.join(GLOBALPARAM['DESTDIR'], "Media", fileinfo['DB']['FanartImg']),
                          'Fanart')
            self.field['Fanart'] = fileinfo['DB']['FanartImg']
            self.field['Poster'] = fileinfo['DB']['MediaImg']
        self.field['Title'] = fileinfo['meta']['showname']
        self.field['EpisodName'] = str(fileinfo['meta']['episodnum']) + ". " + fileinfo['meta']['showtitle']
        self.field['EpisodNameNOCR'] = self.field['EpisodName'].replace("\n", "\\n").replace("\"", "\\\"")
        self.field['EpisodNum'] = fileinfo['meta']['episodnum']
        self.field['Season'] = str(fileinfo['meta']['seasonnum'])
        self.field['Left'] = prev['noext'] + ".html"
        self.field['Right'] = nex['noext'] + ".html"
        self.field['Prev'] = prev['noext'] + ".html"
        self.field['Next'] = nex['noext'] + ".html"
        self.field['Filename'] = self.convertPath(fileinfo['filename'])
        self.field['Year'] = fileinfo['meta']['released']
        self.field['Duration'] = ""
        self.field['Overview'] = fileinfo['meta']['descrip']
        self.field['OverviewNOCR'] = self.field['Overview'].replace("\n", "\\n").replace("\"", "\\\"")
        self.field['Index'] = str(index + 1)


class FileList:
    def __init__(self):
        self.fileinfo = []

    def addfile(self, fileinfo):
        self.fileinfo.append(fileinfo)

    def removefile(self, todel):
        for f in self.fileinfo:
            if f['filename'] == todel:
                self.fileinfo.remove(f)
                return True
        return False

    def getfileallinfo(self, file):
        for f in self.fileinfo:
            if f['filename'] == file:
                return f

    def updatefileinfo(self, file, newinfo, showDB):
        for f in self.fileinfo:
            if f['filename'] == file:
                f['ID'] = newinfo
                f.update(showDB.getinfo(f['filename'], f['dir'], newinfo, "", True))
                return

    def loadparser(self):
        self.index = IndexParser("All.html", GLOBALPARAM['PATHDEF'] + os.path.join("htmlsrc", "Media", "All.html"))
        self.movie = MovieParser(GLOBALPARAM['PATHDEF'] + os.path.join("htmlsrc", "Media", "Movie.html"))
        self.serie = SerieParser(GLOBALPARAM['PATHDEF'] + os.path.join("htmlsrc", "Media", "Serie.html"))

    def generateoutput(self):
        self.loadparser()
        indexall = []
        temp = []
        movies = []
        series = []

        if len(self.fileinfo) == 0:
            return

        self.fileinfo = sorted(self.fileinfo, key=lambda e: e['meta']['showname'])
        for f in self.fileinfo:
            if f['meta']['serie']:
                toadd = True
                for s in series:
                    if s[0]['meta']['showname'] == f['meta']['showname'] and s[0]['meta']['seasonnum'] == f['meta'][
                        'seasonnum']:
                        s.append(f)
                        toadd = False
                if toadd:
                    series.append([f])
            else:
                movies.append(f)
                indexall.append(f)
        # sort series by episod num
        for s in range(len(series)):
            series[s] = sorted(series[s], key=lambda se: int(se['meta']['episodnum']))
            temp.append(series[s][0])
        indexall.extend(temp)

        self.index.dump(indexall)
        if len(movies) > 0:
            nextmovie = movies[0]
            if len(series) > 0:
                prev = series[len(series) - 1][0]
                nextserie = series[0][0]
            else:
                prev = movies[len(movies) - 1]
                nextserie = movies[0]
            for f in range(len(movies)):
                if f + 1 < len(movies):
                    nex = movies[f + 1]
                else:
                    nex = nextserie
                mediaprezgui.updatestatus("Generate output - Creating HTML files - " + movies[f]['noext'])
                self.movie.dump([movies[f]], prev, nex)
                prev = movies[f]
        else:
            nextmovie = series[0][0]
            prev = series[len(series) - 1][0]

        for f in range(len(series)):
            if f + 1 < len(series):
                nex = series[f + 1][0]
            else:
                nex = nextmovie
            mediaprezgui.updatestatus("Generate output - Creating HTML files - " + series[f][0]['noext'])
            self.serie.dump(series[f], prev, nex)
            prev = series[f][0]


class MediaPrez:
    def __init__(self):
        self.globalparamdef()

        self.showDB = ShowDB(GLOBALPARAM['VERBOSE'], os.path.join(GLOBALPARAM['PATHDEF'], TRASHFILE),
                             mediaprezgui.log,
                             GLOBALPARAM['HTTPPROXY'], None, GLOBALPARAM['USEPROXYPHP'])

        self.filelist = FileList()

    def globalparamdef(self):
        GLOBALPARAM['PATHDEF'] = os.path.dirname(os.path.abspath(sys.argv[0])) + os.sep
        GLOBALPARAM['VERBOSE'] = False
        GLOBALPARAM['DESTDIR'] = ""
        GLOBALPARAM['LOCALROOT'] = ""
        GLOBALPARAM['REMOTEROOT'] = ""
        GLOBALPARAM['TAGLAN'] = "en"
        GLOBALPARAM['SUBLAN'] = ""
        GLOBALPARAM['MOVIESET'] = ""
        GLOBALPARAM['FORCERELOAD'] = 0
        GLOBALPARAM['REMOTERELAT'] = 0
        GLOBALPARAM['MOVIEFILTER'] = ".avi,.mkv,.m4v,.mp4"
        GLOBALPARAM['RECURSIVE'] = True
        GLOBALPARAM['SMALL_W'] = 152
        GLOBALPARAM['SMALL_H'] = 241
        GLOBALPARAM['POSTER_W'] = 240
        GLOBALPARAM['POSTER_H'] = 360
        GLOBALPARAM['SCREEN_W'] = 1280
        GLOBALPARAM['SCREEN_H'] = 720
        GLOBALPARAM['HTTPPROXY'] = ""
        GLOBALPARAM['USEPROXYPHP'] = False
        GLOBALPARAM['DEFAULTSUBLAN1'] = "fre"
        GLOBALPARAM['DEFAULTSUBLAN2'] = "eng"

        # if platform.system() == "Windows":
        #       CREATE_NO_WINDOW = 0x8000000

        # read config file
        if os.path.exists(GLOBALPARAM['PATHDEF'] + "config.txt"):
            try:
                execfile(GLOBALPARAM['PATHDEF'] + "config.txt")
            except SystemExit as err:
                print("error parsing config file " + str(err))
                self.clean()
                sys.exit(2)

    def GetGlobalParam(self):
        return GLOBALPARAM;

    def SetGlobalParam(self, GP):
        GLOBALPARAM = GP;

    def usage(self):
        print("""
                todo
                """)

    def processfile(self, file):
        if file == "":
            return False
        mediaprezgui.updatestatus("Processing file " + file)
        fp = self.setfilevar(file)

        # do not erase sub
        if os.path.exists(fp['dir'] + os.sep + fp['noext'] + u".srt"):
            sublan = ""
            fp['substatus'] = ".srt available"
        else:
            sublan = GLOBALPARAM['SUBLAN']
            fp['substatus'] = "No .srt"
        # looking at tag from the web
        fp['ID'] = self.showDB.findFileID(file, None, GLOBALPARAM['TAGLAN'], sublan, GLOBALPARAM['FORCERELOAD'])
        mediaprezgui.log(fp['ID'])
        if len(fp['ID'].IDs) > 1 or fp['ID'].IDs[0] == "":
            fp['ID'] = mediaprezgui.askIDtoUser(fp['filename'], fp['ID'], GLOBALPARAM['SUBLAN'],
                                                GLOBALPARAM['MOVIESET'])
        else:
            fp['ID'].movieset = GLOBALPARAM['MOVIESET']
        mediaprezgui.log(fp['ID'])
        fp.update(
            self.showDB.getinfo(fp['filename'], fp['dir'], fp['ID'], GLOBALPARAM['TAGLAN'], GLOBALPARAM['FORCERELOAD']))
        if fp['ID'].imdb != {} and fp['ID'].imdb[1] != "":
            # download sub
            fp['substatus'] = self.downloadSubtitle(fp['filename'], fp['ID'].imdb, False)

        alreadyin = self.filelist.removefile(file)

        self.filelist.addfile(fp)
        mediaprezgui.updatestatus("File " + file + " done")
        return alreadyin

    def downloadSubtitle(self, filename, imdb, verbose=True):
        try:
            suburl = imdb[1]
        except:
            suburl = ""

        if suburl == "":
            if verbose:
                mediaprezgui.log("No subtitles found", True, mediaprezgui.gui.IDdiag)
            submsg = "No subtitles found"
            mediaprezgui.updateelt2(filename, submsg)
            return submsg

        fp = self.setfilevar(filename)
        if self.showDB.getsubfile(suburl, fp['dir'] + os.sep, fp['dir'] + os.sep + fp['noext'] + u".srt"):
            if verbose:
                mediaprezgui.log("Subtitles downloaded", True, mediaprezgui.gui.IDdiag)
            submsg = imdb[2] + " .srt downloaded"
        else:
            if verbose:
                mediaprezgui.log("Subtitles download error!", True, mediaprezgui.gui.IDdiag)
            submsg = "Download error"
        mediaprezgui.updateelt2(filename, submsg)
        return submsg

    def setfilevar(self, file):
        fp = {}
        fp['filename'] = file
        fp['substatus'] = "NA"
        fp['dir'] = os.path.dirname(os.path.abspath(fp['filename']))
        fp['name'] = os.path.basename(fp['filename'])
        fp['noext'] = os.path.splitext(fp['name'])[0]

        return fp

    def removefile(self, todel):
        return self.filelist.removefile(todel)

    def getfileinfo(self, file):
        return self.filelist.getfileallinfo(file)['ID']

    def getfileallinfo(self, file):
        return self.filelist.getfileallinfo(file)

    def updatefileinfo(self, file, newinfo):
        self.filelist.updatefileinfo(file, newinfo, self.showDB)

    def generateoutput(self):
        mediaprezgui.updatestatus("Generate output")
        try:
            distutils.dir_util.remove_tree(GLOBALPARAM['DESTDIR'], False)
        except:
            pass
        # try several time because the OS needs to realize that the remove is done
        mediaprezgui.updatestatus("Generate output - Creating output dir")
        i = 0
        todo = True
        while todo:
            try:
                i = i + 1
                todo = False
                distutils.dir_util.copy_tree(os.path.join(GLOBALPARAM['PATHDEF'], "htmlsrc") + os.path.sep,
                                             GLOBALPARAM['DESTDIR'] + os.path.sep,
                                             verbose=1)
            except Exception as e:
                msg = str(e)
                if i < 100:
                    todo = True
        if i >= 100:
            mediaprezgui.updatestatus("Error creating output directory:\n" + msg, True)
            return
        mediaprezgui.updatestatus("Generate output - Creating HTML files")
        self.filelist.generateoutput()
        mediaprezgui.updatestatus("Generate output done")
        if sys.platform == "win32":
            os.startfile(os.path.join(GLOBALPARAM['DESTDIR'], "index.html"))
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, os.path.join(GLOBALPARAM['DESTDIR'], "index.html")])


def main(argv):
    try:
        mediaPrez = MediaPrez()
        mediaprezgui.launchGUI("MediaPrez " + GLOBALPARAM['version'], mediaPrez)
    except Exception as e:
        msg = "Global exception " + str(e) + "\n\n" + traceback.format_exc();
        print(msg)
        mediaprezgui.log(msg, True)
        sys.exit(1)


main(sys.argv[1:])

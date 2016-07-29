#! /usr/bin/env python

import sys
import os
import tempfile
import re
import shutil
import platform
import traceback
import iphoneencodegui

sys.path.append('../Lib')
from ShowDB import ShowDB, ShowIDs
import OSTools

GLOBALPARAM = {}
GLOBALPARAM['version'] = u"4.0 Alpha"

TRASHFILE = u"tag.trash"

DEVICECONFSARRAY = [{'encoder': 'handbrake', 'confs': ['HBipad1080p']},
                    {'encoder': 'handbrake', 'confs': ['HBipad720p']}, {'encoder': 'mencoder', 'confs': [u"ipad1080p"]},
                    {'encoder': 'mencoder', 'confs': [u"ipad"]}, {'encoder': 'mencoder', 'confs': [u"iphone"]},
                    {'encoder': 'mencoder', 'confs': [u"iphone", u"ipad1080p"]},
                    {'encoder': 'mencoder', 'confs': [u"ipad", u"ipad1080p"]},
                    {'encoder': 'mencoder', 'confs': [u"iphone", u"ipad", u"ipad1080p"]},
                    {'encoder': 'mencoder', 'confs': [u"subtag"]}, {'encoder': 'mencoder', 'confs': [u"ipadvidcopy"]}]
DEVICECONFSLABELS = [u"iPad3 FullHD (1080p) with HandBrake", u"iPad2/iPhone HD (720p) with HandBrake",
                     u"iPad3 FullHD (1080p)", u"iPad/iPhone4 HD (720p)", u"iPhone3G / iPod Touch SD", u"SD & FullHD",
                     u"HD & FullHD", u"SD, HD and FULLHD", u"Just add subtitles and meta tag",
                     u"Do not transcode but copy video (needs to be x264)"]

HANDBRAKECONFS = {}

REGEX_OUTPUT = {}
REGEX_OUTPUT['mencoder'] = re.compile("([0-9]*)%")
REGEX_OUTPUT['handbrake'] = re.compile("([0-9.]*) %")
REGEX_OUTPUT['MP4Box'] = re.compile("([0-9]*)/")
REGEX_OUTPUT['atomicparsley'] = re.compile("([0-9]*)%")

if sys.version_info > (3, 0):
    def execfile(filename):
        exec (compile(open(filename).read(), filename, 'exec'))


def initfileparam(file):
    fp = {}
    fp['path'] = file
    fp['DESTDIR'] = GLOBALPARAM['DESTDIR']
    fp['FINALDIR'] = GLOBALPARAM['FINALDIR']
    fp['TAGLAN'] = GLOBALPARAM['TAGLAN']
    fp['SUBLAN'] = GLOBALPARAM['SUBLAN']
    fp['MOVIESET'] = GLOBALPARAM['MOVIESET']
    fp['DEVICECONFS'] = GLOBALPARAM['DEVICECONFS']

    GLOBALPARAM['TMPC'] = GLOBALPARAM['TMPC'] + 1
    fp['TMP'] = GLOBALPARAM['TMP'] + unicode(GLOBALPARAM['TMPC'])
    return fp


def globalparamdef():
    GLOBALPARAM['PATHDEF'] = os.path.dirname(os.path.abspath(sys.argv[0])) + os.sep
    GLOBALPARAM['TMP'] = tempfile.mkdtemp(u"iphonencode") + os.sep
    GLOBALPARAM['TMPC'] = 0

    GLOBALPARAM['VERBOSE'] = True

    GLOBALPARAM['USERPARAM'] = ""
    GLOBALPARAM['SHORT'] = ""
    # GLOBALPARAM['SHORT']="-ss 00:12:00 -endpos 0:02:00"
    # GLOBALPARAM['SHORT']=" --start-at 00:12:00 --stop-at 00:13:00 "

    GLOBALPARAM['DESTDIR'] = ""
    GLOBALPARAM['FINALDIR'] = ""
    GLOBALPARAM['DEVICECONFS'] = 0  # see config.txt
    GLOBALPARAM['TAGLAN'] = "en"
    GLOBALPARAM['SUBLAN'] = ""
    GLOBALPARAM['MOVIESET'] = ""
    GLOBALPARAM['SHOWPREFS'] = True

    GLOBALPARAM['HTTPPROXY'] = ""
    GLOBALPARAM['USEPROXYPHP'] = False

    GLOBALPARAM['mplayer'] = "mplayer"
    GLOBALPARAM['mencoder'] = "mencoder"
    GLOBALPARAM['handbrake'] = "handbrake"
    GLOBALPARAM['MP4Box'] = "MP4Box"
    GLOBALPARAM['NBT'] = 1  # number of // encoding to run max


    # read config file
    if os.path.exists(GLOBALPARAM['PATHDEF'] + u"config.txt"):
        try:
            execfile(GLOBALPARAM['PATHDEF'] + u"config.txt")
        except SystemExit as err:
            print("error parsing config file " + unicode(err))
            sys.exit(2)

    if os.path.exists(GLOBALPARAM['PATHDEF'] + u"handbrake.confs"):
        try:
            execfile(GLOBALPARAM['PATHDEF'] + u"handbrake.confs")
        except SystemExit as err:
            print("error parsing handbrake config file " + unicode(err))


def getGlobalParam(newval=None):
    global GLOBALPARAM
    if newval == None:
        return GLOBALPARAM
    else:
        GLOBALPARAM = newval


def mplayer(cmd):
    cmd = "\"" + GLOBALPARAM['mplayer'] + cmd

    if GLOBALPARAM['VERBOSE']:
        logcbk = iphoneencodegui.log
    else:
        logcbk = None

    mplayerout = []
    OSTools.subcall(cmd, logcbk, mplayerout)

    return mplayerout


def mencoder(cmd, progressmsg=""):
    cmd = "\"" + GLOBALPARAM['mencoder'] + cmd

    if GLOBALPARAM['VERBOSE']:
        logcbk = iphoneencodegui.log
    else:
        logcbk = None

    return OSTools.subcall(cmd, logcbk, None, REGEX_OUTPUT['mencoder'],
                           lambda msg: iphoneencodegui.progress(msg, progressmsg), iphoneencodegui.needToStop)


def handbrake(cmd, progressmsg=""):
    cmd = "\"" + GLOBALPARAM['handbrake'] + "\"" + cmd

    if GLOBALPARAM['VERBOSE']:
        logcbk = iphoneencodegui.log
    else:
        logcbk = None

    iphoneencodegui.log(cmd)

    return OSTools.subcall(cmd, logcbk, None, REGEX_OUTPUT['handbrake'],
                           lambda msg: iphoneencodegui.progress(msg, progressmsg), iphoneencodegui.needToStop)


def MP4Box(cmd, progressmsg=""):
    if GLOBALPARAM['VERBOSE']:
        logcbk = iphoneencodegui.log
    else:
        logcbk = None

    cmd = "\"" + GLOBALPARAM['MP4Box'] + cmd

    return OSTools.subcall(cmd, logcbk, None, REGEX_OUTPUT['MP4Box'],
                           lambda msg: iphoneencodegui.progress(msg, progressmsg), iphoneencodegui.needToStop)


def atomicparsley(cmd):
    if GLOBALPARAM['VERBOSE']:
        logcbk = iphoneencodegui.log
    else:
        logcbk = None

    # cmd=u"\""+GLOBALPARAM['atomicparsley']+u"\" "+cmd
    cmd.insert(0, GLOBALPARAM['atomicparsley'])
    print(cmd)

    return OSTools.subcallA(cmd, logcbk, None, REGEX_OUTPUT['atomicparsley'],
                            lambda msg: iphoneencodegui.progress(msg, "Add tag to the file"),
                            iphoneencodegui.needToStop)


def getvideoinfo(fp, name=""):
    if name == "":
        name = fp['path']
    dict = [['ID_VIDEO_FPS=([0-9.]*)', 'fps'], ['ID_VIDEO_WIDTH=([0-9]*)', 'width'],
            ['ID_VIDEO_HEIGHT=([0-9]*)', 'height']]
    cmd = "\" -endpos 0:00:02 -quiet -identify -nosound -vo text -noautosub " + GLOBALPARAM[
        'USERPARAM'] + "\"" + name + u"\""
    mplayerout = mplayer(cmd)

    found = 0
    for l in mplayerout:
        for d, i in dict:
            reg = re.search(d, unicode(l))
            if reg != None:
                fp[i] = float(reg.group(1))
                found = found + 1
    if found != len(dict):
        iphoneencodegui.log("Error parsing video file " + name, True)
        for l in mplayerout:
            iphoneencodegui.log(l)
        return True
    if GLOBALPARAM['VERBOSE']:
        iphoneencodegui.log(
            "Video " + unicode(fp['width']) + "x" + unicode(fp['height']) + " at " + unicode(fp['fps']) + " fps")
    return False


def setfilevar(fp):
    fp['dir'] = os.path.dirname(os.path.abspath(fp['path']))
    fp['name'] = os.path.basename(fp['path'])
    fp['noext'] = os.path.splitext(fp['name'])[0]
    fp['noextclean'] = fp['noext']

    fp['msg'] = u"Encoding " + fp['path']

    fp['subfile'] = u""
    fp['subcmd'] = u""
    if os.path.exists(fp['dir'] + os.sep + fp['noext'] + u".srt"):
        fp['subfile'] = fp['dir'] + os.sep + fp['noext'] + u".srt"
        fp['msg'] = fp['msg'] + u" with subtitle " + fp['subfile']
        fp['subcmd'] = u"-noautosub -sid 666"
        sublan = ""
    else:
        sublan = fp['SUBLAN']

    if fp['DESTDIR'] == "":
        fp['DESTDIR'] = fp['dir']
    fp['noext'] = fp['noext'] + u"_for_" + fp['DEVICECONF']
    fp['dest'] = fp['DESTDIR'] + "/" + fp['noext'] + ".m4v"
    if fp['FINALDIR'] != "":
        fp['finaldest'] = fp['FINALDIR'] + "/" + fp['noext'] + ".m4v"
    else:
        fp['finaldest'] = fp['dest']
    fp['msg'] = fp['msg'] + " to " + fp['finaldest']

    if getvideoinfo(fp):
        return True
    if fp['fps'] < 24:
        iphoneencodegui.log("Correct fps because detected fps is " + unicode(fp['fps']))
        fp['fps'] = 24
        fp['FPSCMD'] = "-ofps 24000/1001"
    else:
        fp['FPSCMD'] = ""
    global showDB

    IDs = showDB.findFileID(fp['path'], None, fp['TAGLAN'], sublan, False)
    iphoneencodegui.log(IDs)
    if len(IDs.IDs) == 1 and IDs.IDs[0] != "":
        fp['ID'] = IDs
        fp['DIAGIDPTR'] = None
        fp['IMDB'] = IDs.imdb
    else:
        fp['ID'] = ""
        fp['DIAGIDPTR'] = iphoneencodegui.askIDtoUser(fp['name'], IDs)

    return False


def encodefile(fp):
    iphoneencodegui.log(fp['msg'])

    if os.path.exists(fp['finaldest']):
        iphoneencodegui.log("Output file " + fp['finaldest'] + " exists already!", True)
        return True

    if fp['DEVICECONF'] == "subtag":
        # shutil.copy(fp['path'],fp['TMP']+"iphoneencode.m4v")
        iphoneencodegui.globalprogress(1, 97)
        iphoneencodegui.filewithfeedback(fp['path'], fp['TMP'] + "iphoneencode.m4v", "copy", "Copy")
        return False

    if fp['DEVICECONFS']['encoder'] == 'mencoder':
        iphoneencodegui.log("Encoding using mencoder")
        cmd = "\" " + GLOBALPARAM['SHORT'] + " -include " + "\"" + GLOBALPARAM[
            'PATHDEF'] + "iphoneencode.conf\" -msglevel identify=6 -profile " + fp['DEVICECONF'] + " -of avi " + fp[
                  'subcmd'] + " " + fp['FPSCMD'] + " " + GLOBALPARAM['USERPARAM'] + " -o \"" + fp[
                  'TMP'] + "iphoneencode.avi\" \"" + fp['path'] + "\""
        iphoneencodegui.globalprogress(1, 90)
        if mencoder(cmd, "Encoding"):
            return True

        iphoneencodegui.log("Put in m4v")
        cmd = "\" -include \"" + GLOBALPARAM[
            'PATHDEF'] + "iphoneencode.conf\" -msglevel identify=6 -profile ipadcopy " + GLOBALPARAM[
                  'USERPARAM'] + " -o \"" + fp['TMP'] + "iphoneencode.m4v\" \"" + fp['TMP'] + "iphoneencode.avi\""
        iphoneencodegui.globalprogress(90, 97)
        status = mencoder(cmd, "Put in m4v")
        os.remove(fp['TMP'] + "iphoneencode.avi")
    else:
        iphoneencodegui.log("Encoding using HandBrake")

        # file in & out
        cmd = " -i \"" + fp['path'] + "\"" + GLOBALPARAM['SHORT']
        # global param
        cmd = cmd + HANDBRAKECONFS[fp['DEVICECONF']]
        # subtitle TODO not working so far
        # if fp['subfile'] != "":
        #	cmd=cmd+" --srt-file \""+fp['subfile']+"\" "
        #	fp['subfile']=""
        cmd = cmd + " -o \"" + fp['TMP'] + "iphoneencode.m4v\""

        iphoneencodegui.globalprogress(1, 97)
        status = handbrake(cmd, "Handbrake encoding")

    return status


def fetchsub(fp):
    try:
        if fp['subfile'] == "":
            if fp['IMDB'] != {} and fp['IMDB'][1] != "":
                if showDB.getsubfile(fp['IMDB'][1], GLOBALPARAM['TMP'],
                                     fp['dir'] + os.sep + fp['noextclean'] + u".srt"):
                    fp['subfile'] = fp['dir'] + os.sep + fp['noextclean'] + u".srt"
    except:
        return


def addsub(fp):
    if fp['subfile'] == "":
        return

    iphoneencodegui.log("Adding subtitle")
    cmd = "\" -add \"" + fp['subfile'] + ":lang=fra:layout=0x60x0x-1:group=2\" \"" + fp[
        'TMP'] + "iphoneencode.m4v\" -out \"" + fp['TMP'] + "iphoneencodesub.m4v\""
    if MP4Box(cmd, "Adding subtitle"):
        # Try to convert to UTF8
        back = fp['dir'] + os.sep + fp['noextclean'] + u"_backup.srt"
        shutil.move(fp['subfile'], back)
        subin = open(back, "r")
        subout = open(fp['subfile'], "w")
        for l in subin:
            c = unicode(l, "iso-8859-1")
            subout.write(c.encode("UTF8"))
        subin.close()
        subout.close()
        if MP4Box(cmd, "Adding subtitle"):
            return True
    shutil.move(fp['TMP'] + "iphoneencodesub.m4v", fp['TMP'] + "iphoneencode.m4v")


def addtag(fp):
    temploc = GLOBALPARAM['TMP'] + fp['noext'] + ".m4v"
    shutil.move(fp['TMP'] + "iphoneencode.m4v", temploc)
    iphoneencodegui.log("Tag m4v")
    iphoneencodegui.progress(100, msg="Add tag")
    getvideoinfo(fp, temploc)
    HD = fp['width'] > 1000
    if fp['ID'] == "" and fp['DIAGIDPTR'] != None:
        fp['ID'] = iphoneencodegui.getIDfromUser(fp['DIAGIDPTR'])
    iphoneencodegui.log(u"ID " + unicode(fp['ID']))
    showDB.tagfile(temploc, fp['dir'], HD, fp['ID'], fp['TAGLAN'])

    return False


def movingfile(fp):
    iphoneencodegui.log("Moving file")
    iphoneencodegui.progress(100, msg="Moving")
    try:
        iphoneencodegui.log(GLOBALPARAM['TMP'] + fp['noext'] + ".m4v " + fp['dest'])
        # shutil.move(GLOBALPARAM['TMP']+fp['noext']+".m4v", fp['dest'])
        iphoneencodegui.filewithfeedback(GLOBALPARAM['TMP'] + fp['noext'] + ".m4v", fp['dest'], "move", "Moving")
        if fp['dest'] != fp['finaldest']:
            # shutil.move(fp['dest'],fp['finaldest'])
            iphoneencodegui.filewithfeedback(fp['dest'], fp['finaldest'], "move", "Moving")
    except Exception, e:
        iphoneencodegui.log("Error moving the file!, trying to move it in the same folder than source \n" + unicode(e),
                            True)
        fp['dest'] = fp['dir'] + "/" + fp['noext'] + ".m4v"
        try:
            # shutil.move(GLOBALPARAM['TMP']+fp['noext']+".m4v", fp['dest'])
            iphoneencodegui.filewithfeedback(GLOBALPARAM['TMP'] + fp['noext'] + ".m4v", fp['dest'], "move", "Moving")
        except Exception, e:
            iphoneencodegui.log("There is really an issue, cannot move it there too!!! \n" + unicode(e), True)
        return True

    return False


def processfile(fp):
    # 1
    iphoneencodegui.globalprogress(0, 1)
    if setfilevar(fp):
        return True

    # if GLOBALPARAM['VERBOSE']:
    #		iphoneencodegui.log(fp)
    # 2
    if encodefile(fp):
        return True
    # 3
    iphoneencodegui.globalprogress(97, 98)

    # try to fetch sub if needed
    fetchsub(fp)
    # even if the add sub fail, continue
    addsub(fp)

    # 4
    iphoneencodegui.globalprogress(98, 99)
    if addtag(fp):
        return True
    # 5
    iphoneencodegui.globalprogress(99, 100)
    return movingfile(fp)


def transcodefile(file, fileparamgui={}):
    iphoneencodegui.log("Transcoding " + file)
    fp = initfileparam(file)

    if fileparamgui != {}:
        fp['DESTDIR'] = fileparamgui['dest']
        fp['FINALDIR'] = fileparamgui['destfinal']
        fp['DEVICECONFS'] = fileparamgui['deviceconfs']
        fp['TAGLAN'] = fileparamgui['taglan']
        fp['SUBLAN'] = fileparamgui['sublan']
        fp['MOVIESET'] = fileparamgui['movieset']

    fp['DEVICECONFS'] = DEVICECONFSARRAY[fp['DEVICECONFS']]

    error = False
    for fp['DEVICECONF'] in fp['DEVICECONFS']['confs']:
        error = processfile(fp)
        if error:
            break

    if error:
        iphoneencodegui.log(file + " not done due to error!", True)
    else:
        iphoneencodegui.log(file + " done!")


def cleantempfile():
    if not GLOBALPARAM['VERBOSE']:
        shutil.rmtree(GLOBALPARAM['TMP'])


def main(argv):
    try:
        globalparamdef()

        global showDB
        showDB = ShowDB(GLOBALPARAM['VERBOSE'], GLOBALPARAM['PATHDEF'] + os.sep + TRASHFILE, iphoneencodegui.log,
                        GLOBALPARAM['HTTPPROXY'], atomicparsley, GLOBALPARAM['USEPROXYPHP'])

        iphoneencodegui.launchGUI("iphonencode " + GLOBALPARAM['version'], GLOBALPARAM['NBT'], DEVICECONFSLABELS,
                                  transcodefile, cleantempfile, getGlobalParam, showDB)
    except Exception, e:
        msg = "Global exception " + unicode(e) + "\n\n" + traceback.format_exc();
        print(msg)
        logcbk(msg, True)
        sys.exit(1)


main(sys.argv[1:])

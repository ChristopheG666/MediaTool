import os
import re
import sys

toclean = [".nfo", ".Info", ".jpg", ".srt"]
movieext = [".avi", ".mkv", ".m4v", ".mp4"]

directory = "."
if len(sys.argv) > 1:
    directory = sys.argv[1]

refanart = re.compile("(.*)\.Fanart$")

filelist = []
for root, _, files in os.walk(directory, topdown=False):
    for name in files:
        filelist.append({'dir': root, 'name': name, 'path': os.path.join(root, name),
                         'ext': os.path.splitext(name)[1], 'noext': os.path.splitext(name)[0]})

todel = []
for f in filelist:
        if f['ext'] in toclean:
            fanart = refanart.match(f['noext'])
            if fanart is not None:
                f['noext'] = fanart.group(1)
            match = [fm for fm in filelist if f['noext'] == fm['noext'] and fm['ext'] in movieext]
            if len(match) > 0:
                print("Do not delete {0} because file {1}".format(f['name'], ",".join([fm['name'] for fm in match])))
                continue
            print("To del {0}".format(f['name']))
            todel.append(f['path'])

if len(todel) > 0:
    print("Are you sure you want to delete:\n{0}\n(y/n):".format("\n".join(todel)))
    confirm = raw_input()

    if confirm.lower() == "y":
        for f in todel:
            os.remove(f)
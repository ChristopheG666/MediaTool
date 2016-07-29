import os
import re
import sys

toclean = [".nfo", ".Info", ".jpg", ".srt"]
movieext = [".avi", ".mkv", ".m4v", ".mp4"]

directory = "."
if len(sys.argv) > 1:
    directory = sys.argv[1]

refanart = re.compile("(.*)\.Fanart$")

todel = []

for root, _, files in os.walk(directory, topdown=False):
    for name in files:
        filesplit = os.path.splitext(name)
        if filesplit[1] in toclean:
            filenamenoext = filesplit[0]
            fanart = refanart.match(filenamenoext)
            if fanart is not None:
                filenamenoext = fanart.group(1)
            filename = os.path.join(directory, filenamenoext)
            found = False
            for mext in movieext:
                if os.path.exists(filename + mext):
                    found = True
                    break

            if found:
                print("Do not delete {0} because file {1}".format(os.path.join(root, name), filename + mext))
                continue
            print("To del {0}".format(os.path.join(root, name)))
            todel.append(os.path.join(root, name))


print("Are you sure you want to delete:\n{0}\n(y/n):".format("\n".join(todel)))
confirm = raw_input()

if confirm.lower() == "y":
    for f in todel:
        os.remove(f)
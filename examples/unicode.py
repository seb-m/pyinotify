import os
from pyinotify import *

# create path
path = u'/tmp/test\u0444'
if not os.path.isdir(path):
    os.mkdir(path)

log.setLevel(10)
wm = WatchManager()
notifier = Notifier(wm)

wdd = wm.add_watch(path, IN_OPEN)
wm.update_watch(wdd[path], ALL_EVENTS)

notifier.loop()

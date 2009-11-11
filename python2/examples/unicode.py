# -*- coding: utf-8 -*-
import os
import sys
import pyinotify


# create path
#path = u'/tmp/test\u0444'
path = '/tmp/testф'
path = unicode(path, sys.getfilesystemencoding())

if not os.path.isdir(path):
    os.mkdir(path)

pyinotify.log.setLevel(10)
wm = pyinotify.WatchManager()
notifier = pyinotify.Notifier(wm)

wdd = wm.add_watch(path, pyinotify.IN_OPEN)
wm.update_watch(wdd[path], pyinotify.ALL_EVENTS)

notifier.loop()

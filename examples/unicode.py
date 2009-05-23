from pyinotify import *

log.setLevel(10)
wm = WatchManager()
notifier = Notifier(wm)
path = u'/tmp'
wdd = wm.add_watch(path, IN_OPEN)
wm.update_watch(wdd[path], ALL_EVENTS)

notifier.loop()

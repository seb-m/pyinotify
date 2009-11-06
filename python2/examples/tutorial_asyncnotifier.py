# AsyncNotifier example from tutorial
#
# See: http://trac.dbzteam.org/pyinotify/wiki/Tutorial
#
from pyinotify import WatchManager, AsyncNotifier, \
     ThreadedNotifier, ProcessEvent, IN_DELETE, \
     IN_CREATE
import asyncore

wm = WatchManager()  # Watch Manager
mask = IN_DELETE | IN_CREATE  # watched events

class PTmp(ProcessEvent):
    def process_IN_CREATE(self, event):
        print "Creating:", event.pathname

    def process_IN_DELETE(self, event):
        print "Removing:", event.pathname

p = PTmp()
notifier = AsyncNotifier(wm, p)
wdd = wm.add_watch('/tmp', mask, rec=True)

asyncore.loop()

# Notifier example from tutorial
#
# See: http://trac.dbzteam.org/pyinotify/wiki/Tutorial
#
from pyinotify import WatchManager, Notifier, \
    ThreadedNotifier, ProcessEvent, IN_DELETE, \
    IN_CREATE

wm = WatchManager()  # Watch Manager
mask = IN_DELETE | IN_CREATE  # watched events

class PTmp(ProcessEvent):
    def process_IN_CREATE(self, event):
        print "Creating:", event.pathname

    def process_IN_DELETE(self, event):
        print "Removing:", event.pathname

p = PTmp()
notifier = Notifier(wm, p)
wdd = wm.add_watch('/tmp', mask, rec=True)

notifier.loop()

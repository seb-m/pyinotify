# Notifier example from tutorial
#
# See: http://trac.dbzteam.org/pyinotify/wiki/Tutorial
#
import pyinotify

wm = pyinotify.WatchManager()  # Watch Manager
mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE  # watched events

class HandleEvents(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        print "Creating:", event.pathname

    def process_IN_DELETE(self, event):
        print "Removing:", event.pathname

p = HandleEvents()
notifier = pyinotify.Notifier(wm, p)
wdd = wm.add_watch('/tmp', mask, rec=True)

notifier.loop()

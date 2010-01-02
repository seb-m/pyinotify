# ThreadedNotifier example from tutorial
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


#log.setLevel(10)
notifier = pyinotify.ThreadedNotifier(wm, HandleEvents())
notifier.start()

wdd = wm.add_watch('/tmp', mask, rec=True)
wm.rm_watch(wdd.values())

notifier.stop()

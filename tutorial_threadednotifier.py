# ThreadedNotifier example from tutorial
#
# See: http://trac.dbzteam.org/pyinotify/wiki/Tutorial
#
from pyinotify import WatchManager, Notifier, \
    ThreadedNotifier, ProcessEvent, IN_DELETE, \
    IN_CREATE, log

wm = WatchManager()  # Watch Manager
mask = IN_DELETE | IN_CREATE  # watched events

class PTmp(ProcessEvent):
    def process_IN_CREATE(self, event):
        print "Creating:", event.pathname

    def process_IN_DELETE(self, event):
        print "Removing:", event.pathname


#log.setLevel(10)
notifier = ThreadedNotifier(wm, PTmp())
notifier.start()

wdd = wm.add_watch('/tmp', mask, rec=True)
wm.rm_watch(wdd.values())

notifier.stop()

import pyinotify
from tornado.ioloop import IOLoop

wm = pyinotify.WatchManager() # Watch Manager
mask = pyinotify.IN_MODIFY

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_MODIFY(self, event):
        # We have explicitely registered for this kind of event.
        print '\t', event.pathname, ' -> written'
    def process_default(self, event):
        print event

ioloop = IOLoop.instance()
notifier = pyinotify.TornadoAsyncNotifier(wm, ioloop)
#daemon.pids['nginx']
wdd = wm.watch_transient_file('/tmp/test_file', pyinotify.IN_MODIFY, EventHandler)

ioloop.start()
from pyinotify import *


class Log(ProcessEvent):
    def my_init(self, pathname):
        self._fileobj = file(pathname, 'w')

    def process_default(self, event):
        self._fileobj.write(str(event) + '\n')
        self._fileobj.flush()

class TrackMofications(ProcessEvent):
    def process_IN_MODIFY(self, event):
        print 'IN_MODIFY'

    def process_default(self, event):
        pass

class Empty(ProcessEvent):
    def my_init(self, msg):
        self._msg = msg

    def process_default(self, event):
        print self._msg


#log.setLevel(10)
f = '/var/log/pyinotify_log'
wm = WatchManager()
# It is important to give extra arguments like 'pathname' with
# their keyword.
notifier = Notifier(wm, Empty(TrackMofications(Log(pathname=f)),
                              msg='outtee chained function'))
wm.add_watch('/tmp', ALL_EVENTS)
notifier.loop()

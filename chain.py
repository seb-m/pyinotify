# Example
#
from pyinotify import *


class Log(ProcessEvent):
    def my_init(self, fileobj):
        self._fileobj = fileobj

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
fo = file('/var/log/pyinotify_log', 'w')
wm = WatchManager()
# It is important to pass named extra arguments like 'fileobj'.
notifier = Notifier(wm,
                    default_proc_fun=Empty(TrackMofications(Log(fileobj=fo)),
                                           msg='outtee chained function'))
wm.add_watch('/tmp', ALL_EVENTS)
notifier.loop()
fo.close()

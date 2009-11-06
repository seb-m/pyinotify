# Example: monitors events and logs them into a log file.
#
from pyinotify import *

class Log(ProcessEvent):
    def my_init(self, fileobj):
        """
        Method automatically called from ProcessEvent.__init__(). Additional
        keyworded arguments passed to ProcessEvent.__init__() are then
        delegated to my_init(). This is the case for fileobj.
        """
        self._fileobj = fileobj

    def process_default(self, event):
        self._fileobj.write(str(event) + '\n')
        self._fileobj.flush()

class TrackModifications(ProcessEvent):
    def process_IN_MODIFY(self, event):
        print 'IN_MODIFY'

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
                    default_proc_fun=Empty(TrackModifications(Log(fileobj=fo)),
                                           msg='outtee chained function'))
wm.add_watch('/tmp', ALL_EVENTS)
notifier.loop()
fo.close()

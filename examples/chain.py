# Example
#
# This example logs the observed events into a log file.
from pyinotify import *

class Log(ProcessEvent):
    def my_init(self, fileobj):
        """
        Template method automatically called from ProcessEvent.__init__().
        And keyworded arguments passed to ProcessEvent.__init__() are delegated
        to my_init().
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

# Example: monitors events and logs them into a log file.
#
import pyinotify

class Log(pyinotify.ProcessEvent):
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

class TrackModifications(pyinotify.ProcessEvent):
    def process_IN_MODIFY(self, event):
        print 'IN_MODIFY'

class Empty(pyinotify.ProcessEvent):
    def my_init(self, msg):
        self._msg = msg

    def process_default(self, event):
        print self._msg


# pyinotify.log.setLevel(10)
fo = file('/var/log/pyinotify_log', 'w')
try:
    wm = pyinotify.WatchManager()
    # It is important to pass named extra arguments like 'fileobj'.
    handler = Empty(TrackModifications(Log(fileobj=fo)), msg='Outer chained method')
    notifier = pyinotify.Notifier(wm, default_proc_fun=handler)
    wm.add_watch('/tmp', pyinotify.ALL_EVENTS)
    notifier.loop()
finally:
    fo.close()

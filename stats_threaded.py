# Example
#
import time
from pyinotify import *

# Do the same thing than stats.py but with a ThreadedNotifier's
# instance.
# This example illustrates the use of this class but the recommanded
# implementation is whom of stats.py


class Identity(ProcessEvent):

    def process_default(self, event):
        # Does nothing, just to demonstrate how stuffs could be done
        # after having processed statistics.
        pass


wm = WatchManager()
s = Stats() # Stats is a subclass of ProcessEvent
notifier = ThreadedNotifier(wm, default_proc_fun=Identity(s))
notifier.start()
wm.add_watch('/tmp/', ALL_EVENTS, rec=True, auto_add=True)

while True:
    try:
        print repr(s)
        print
        print s
        print
        time.sleep(5)
    except KeyboardInterrupt:
        print 'stop monitoring...'
        notifier.stop()
        break
    except Exception, err:
        print err

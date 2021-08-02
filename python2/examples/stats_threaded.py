# Example: prints statistics (threaded version).
#
import time
import pyinotify

# Do the same thing than stats.py but with a ThreadedNotifier's
# instance.
# This example illustrates the use of this class but the recommended
# implementation is whom of stats.py

class Identity(pyinotify.ProcessEvent):
    def process_default(self, event):
        # Does nothing, just to demonstrate how stuffs could be done
        # after having processed statistics.
        print 'Does nothing.'

# Thread #1
wm1 = pyinotify.WatchManager()
s1 = pyinotify.Stats() # Stats is a subclass of ProcessEvent
notifier1 = pyinotify.ThreadedNotifier(wm1, default_proc_fun=Identity(s1))
notifier1.start()
wm1.add_watch('/tmp/', pyinotify.ALL_EVENTS, rec=True, auto_add=True)

# Thread #2
wm2 = pyinotify.WatchManager()
s2 = pyinotify.Stats() # Stats is a subclass of ProcessEvent
notifier2 = pyinotify.ThreadedNotifier(wm2, default_proc_fun=Identity(s2))
notifier2.start()
wm2.add_watch('/var/log/', pyinotify.ALL_EVENTS, rec=False, auto_add=False)

while True:
    try:
        print "Thread 1", repr(s1)
        print s1
        print "Thread 2", repr(s2)
        print s2
        print
        time.sleep(5)
    except KeyboardInterrupt:
        notifier1.stop()
        notifier2.stop()
        break
    except:
        notifier1.stop()
        notifier2.stop()
        raise

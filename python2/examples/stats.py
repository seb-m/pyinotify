# Example: prints statistics.
#
import pyinotify

class Identity(pyinotify.ProcessEvent):
    def process_default(self, event):
        # Does nothing, just to demonstrate how stuffs could trivially
        # be accomplished after having processed statistics.
        print 'Does nothing.'

def on_loop(notifier):
    # notifier.proc_fun() is Identity's instance
    s_inst = notifier.proc_fun().nested_pevent()
    print repr(s_inst), '\n', s_inst, '\n'


wm = pyinotify.WatchManager()
# Stats is a subclass of ProcessEvent provided by pyinotify
# for computing basics statistics.
s = pyinotify.Stats()
notifier = pyinotify.Notifier(wm, default_proc_fun=Identity(s), read_freq=5)
wm.add_watch('/tmp/', pyinotify.ALL_EVENTS, rec=True, auto_add=True)
notifier.loop(callback=on_loop)

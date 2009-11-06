import pyinotify

class MoveEventHandler(pyinotify.ProcessEvent):
    def my_init(self):
        self.in_moved_from = {}  # dict of {src_path: 1}

    def process_IN_MOVED_FROM(self, event):
        self.in_moved_from[event.pathname] = 1

    def process_IN_MOVED_TO(self, event):
        if hasattr(event, 'src_pathname'):
            try:
                del self.in_moved_from[event.src_pathname]
            except NameError:
                pass
            print event.src_pathname, 'moved to', event.pathname
        else:
            print '<unknown> moved to', event.pathname

    def process_default(self, event):
        # Ignoring everything else.
        pass

def handle_orphans(notifier):
    moved = notifier.proc_fun().in_moved_from
    for path in moved:
        print path, 'moved to <unknown>'
    # Clear the dictionnary
    moved.clear()


wm = pyinotify.WatchManager()
meh = MoveEventHandler()
# Use read_freq and timeout to be sure to call the callback function
# handle_orphans() regularly. A path will be declared orphan after
# an interval of [1, 5] seconds.
notifier = pyinotify.Notifier(wm, default_proc_fun=meh,
                              read_freq=5, timeout=4000)
wm.add_watch('/tmp/', pyinotify.ALL_EVENTS, rec=True, auto_add=True)
notifier.loop(callback=handle_orphans)

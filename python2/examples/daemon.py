# Example: daemonize pyinotify's notifier.
#
# Requires Python >= 2.5
import functools
import sys
import pyinotify

class Counter(object):
    """
    Simple counter.
    """
    def __init__(self):
        self.count = 0
    def plusone(self):
        self.count += 1

def on_loop(notifier, counter):
    """
    Dummy function called after each event loop, this method only
    ensures the child process eventually exits (after 5 iterations).
    """
    if counter.count > 4:
        # Loops 5 times then exits.
        sys.stdout.write("Exit\n")
        notifier.stop()
        sys.exit(0)
    else:
        sys.stdout.write("Loop %d\n" % counter.count)
        counter.plusone()

wm = pyinotify.WatchManager()
notifier = pyinotify.Notifier(wm)
wm.add_watch('/tmp', pyinotify.ALL_EVENTS)
on_loop_func = functools.partial(on_loop, counter=Counter())

# Notifier instance spawns a new process when daemonize is set to True. This
# child process' PID is written to /tmp/pyinotify.pid (it also automatically
# deletes it when it exits normally). If no custom pid_file is provided it
# would write it more traditionally under /var/run/. Note that in both cases
# the caller must ensure the pid file doesn't exist when this method is called
# othewise it will raise an exception. /tmp/stdout.txt is used as stdout 
# stream thus traces of events will be written in it. callback is the above 
# function and will be called after each event loop.
try:
    notifier.loop(daemonize=True, callback=on_loop_func,
                  pid_file='/tmp/pyinotify.pid', stdout='/tmp/stdout.txt')
except pyinotify.NotifierError, err:
    print >> sys.stderr, err

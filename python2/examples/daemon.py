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
# deletes it when it exits normally). Note that this tmp location is just for
# the sake of the example to avoid requiring administrative rights in order
# to run this example. But by default if no explicit pid_file parameter is
# provided it will default to its more traditional location under /var/run/.
# Note that in both cases the caller must ensure the pid file doesn't exist
# before this method is called otherwise it will raise an exception.
# /tmp/pyinotify.log is used as log file to dump received events. Likewise
# in your real code choose a more appropriate location for instance under
# /var/log (this file may contain sensitive data). Finally, callback is the
# above function and will be called after each event loop.
try:
    notifier.loop(daemonize=True, callback=on_loop_func,
                  pid_file='/tmp/pyinotify.pid', stdout='/tmp/pyinotify.log')
except pyinotify.NotifierError, err:
    print >> sys.stderr, err

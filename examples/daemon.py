# Example: daemonize pyinotify's notifier.
#
import pyinotify

wm = pyinotify.WatchManager()
notifier = pyinotify.Notifier(wm)
wm.add_watch('/tmp', pyinotify.ALL_EVENTS)
notifier.loop(daemonize=True, pid_file='/tmp/pyinotify.pid', force_kill=True,
              stdout='/tmp/stdout.txt')

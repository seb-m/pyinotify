# Example: loops monitoring events forever.
#
import pyinotify

wm = pyinotify.WatchManager()
notifier = pyinotify.Notifier(wm)
wm.add_watch('/tmp', pyinotify.ALL_EVENTS)
notifier.loop()

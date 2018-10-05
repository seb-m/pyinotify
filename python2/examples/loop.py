# Example: loops monitoring events forever.
#
import pyinotify

# Instantiate a new WatchManager (will be used to store watches).
wm = pyinotify.WatchManager()
# Associate this WatchManager with a Notifier (will be used to report and
# process events).
notifier = pyinotify.Notifier(wm)
# Add a new watch on /tmp for ALL_EVENTS.
wm.add_watch('/tmp', pyinotify.ALL_EVENTS)
# Loop forever and handle events.
notifier.loop()

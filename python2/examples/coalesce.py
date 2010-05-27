# Example: coalesce events.
#
import pyinotify

# For instance when this example is run with this command:
#   cd /tmp && echo "test" > test && echo "test" >> test
#
# It will give the following result when notifier.coalesce_events(False) is called
# (default behavior, same as if we had not called this method):
#
#   <Event dir=False mask=0x100 maskname=IN_CREATE name=test path=/tmp pathname=/tmp/test wd=1 >
#   <Event dir=False mask=0x20 maskname=IN_OPEN name=test path=/tmp pathname=/tmp/test wd=1 >
#   <Event dir=False mask=0x2 maskname=IN_MODIFY name=test path=/tmp pathname=/tmp/test wd=1 >
#   <Event dir=False mask=0x8 maskname=IN_CLOSE_WRITE name=test path=/tmp pathname=/tmp/test wd=1 >
#   <Event dir=False mask=0x20 maskname=IN_OPEN name=test path=/tmp pathname=/tmp/test wd=1 >
#   <Event dir=False mask=0x2 maskname=IN_MODIFY name=test path=/tmp pathname=/tmp/test wd=1 >
#   <Event dir=False mask=0x8 maskname=IN_CLOSE_WRITE name=test path=/tmp pathname=/tmp/test wd=1 >
#
# And will give the following result when notifier.coalesce_events() is called:
#
#   <Event dir=False mask=0x100 maskname=IN_CREATE name=test path=/tmp pathname=/tmp/test wd=1 >
#   <Event dir=False mask=0x20 maskname=IN_OPEN name=test path=/tmp pathname=/tmp/test wd=1 >
#   <Event dir=False mask=0x2 maskname=IN_MODIFY name=test path=/tmp pathname=/tmp/test wd=1 >
#   <Event dir=False mask=0x8 maskname=IN_CLOSE_WRITE name=test path=/tmp pathname=/tmp/test wd=1 >

wm = pyinotify.WatchManager()
# Put an arbitrary large value (10 seconds) to aggregate together a larger
# chunk of events. For instance if you repeat several times a given action
# on the same file its events will be coalesced into a signe event and only
# one event of this type will be reported (for this period).
notifier = pyinotify.Notifier(wm, read_freq=10)
# Enable coalescing of events.
notifier.coalesce_events()
wm.add_watch('/tmp', pyinotify.ALL_EVENTS)
notifier.loop()

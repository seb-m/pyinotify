# Example
#

# Overrides default behavior and raise exception on add_watch, update_watch,
# rm_watch errors.

import pyinotify

wm = pyinotify.WatchManager()


# default behavior, don't complain but keep trace of error in log and result
r = wm.add_watch(['/tmp', '/tmp-do-not-exist'], pyinotify.ALL_EVENTS)
print r


# quiet=False raise exception
try:
    wm.add_watch(['/tmp', '/tmp-do-not-exist'], 
                     pyinotify.ALL_EVENTS, quiet=False)
except pyinotify.WatchManagerError, err:
    print err, err.wmd


# quiet=False raise exception
try:
    wm.update_watch(42, mask=0x42, quiet=False)
except pyinotify.WatchManagerError, err:
    print err, err.wmd


# quiet=False raise exception
try:
    wm.rm_watch(42, quiet=False)
except pyinotify.WatchManagerError, err:
    print err, err.wmd


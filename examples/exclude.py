# Example
#
import pyinotify
import os

excl_file = os.path.join(os.getcwd(), 'exclude.patterns')

wm = pyinotify.WatchManager()
notifier = pyinotify.Notifier(wm)


### Method 1:
# Exclude filter object
excl = pyinotify.ExcludeFilter({excl_file: ('excl_lst1', 'excl_lst2')})
# Add watches
wm.add_watch(['/etc/*', '/var'], pyinotify.ALL_EVENTS,
             rec=True, do_glob=True, exclude_filter=excl)


### Method 2 (Equivalent)
wm.add_watch('/etc/*', pyinotify.ALL_EVENTS, rec=True, do_glob=True,
             exclude_filter=pyinotify.ExcludeFilter({excl_file:('excl_lst1',)}))
wm.add_watch('/var', pyinotify.ALL_EVENTS, rec=True,
             exclude_filter=pyinotify.ExcludeFilter({excl_file:('excl_lst2',)}))


notifier.loop()

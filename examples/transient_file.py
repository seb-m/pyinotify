# Example: monitors transient files.
#
# Run this code, then run transient_file.sh in another shell.
from pyinotify import *

class ProcessTransientFile(ProcessEvent):

    def process_IN_MODIFY(self, event):
        # We have explicitely registered for this kind of event.
        print '\t', event.pathname, ' -> written'

    def process_default(self, event):
        # Implicitely IN_CREATE and IN_DELATE are watched too. You can
        # ignore them and provide an empty process_default or you can
        # process them, either with process_default or their dedicated
        # method (process_IN_CREATE, process_IN_DELETE) which would
        # override process_default.
        print 'default: ', event.maskname


wm = WatchManager()
notifier = Notifier(wm)
# In this case you must give the class object (ProcessTransientFile)
# as last parameter not a class instance.
wm.watch_transient_file('/tmp/test1234', IN_MODIFY, ProcessTransientFile)
notifier.loop()

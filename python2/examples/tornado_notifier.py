import pyinotify
from tornado.ioloop import IOLoop


def handle_read_callback(notifier):
    """
    Just stop receiving IO read events after the first
    iteration (unrealistic example).
    """
    print('handle_read callback')
    notifier.io_loop.stop()


wm = pyinotify.WatchManager()
ioloop = IOLoop.instance()
notifier = pyinotify.TornadoAsyncNotifier(wm, ioloop,
                                          callback=handle_read_callback)
wm.add_watch('/tmp', pyinotify.ALL_EVENTS)
ioloop.start()
ioloop.close()
notifier.stop()

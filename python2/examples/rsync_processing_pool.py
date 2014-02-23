#!/usr/bin/env python

"""A working example of using pyinotify to trigger data reduction.

A multiprocessing pool is used to perform the reduction in
an asynchronous and parallel fashion.
"""
import sys
import multiprocessing
import logging, logging.handlers
import os
import shutil
import time
import pyinotify

logger = logging.getLogger()

class options():
    """Dummy class serving as a placeholder for argparse handling."""
    watch_dir = "test/rsync_to_here"
    log_dir = "test/"
    output_dir = "test/output"
    nthreads = 4

class RsyncNewFileHandler(pyinotify.ProcessEvent):
    """Identifies new rsync'ed files and passes their path for processing.

    rsync creates temporary files with a `.` prefix and random 6 letter suffix,
    then renames these to the original filename when the transfer is complete.
    To reliably catch (only) new transfers while coping with this file-shuffling,
    we must do a little bit of tedious file tracking, using
    the internal dict `tempfiles`.
    Note we only track those files satisfying the condition
    ``file_predicate(basename)==True``.

    """
    def my_init(self, nthreads, file_predicate, file_processor):
        self.mask = pyinotify.IN_CREATE | pyinotify.IN_MOVED_TO
        self.tempfiles = {}
        self.predicate = file_predicate
        self.process = file_processor

    def process_IN_CREATE(self, event):
        original_filename = os.path.splitext(event.name[1:])[0]
        if self.predicate(original_filename):
            logger.debug("Transfer started, tempfile at:\n\t%s\n",
                         event.pathname)
            self.tempfiles[original_filename] = event.pathname

    def process_IN_MOVED_TO(self, event):
        #Now rsync has renamed the file to drop the temporary suffix.
        #NB event.name == basename(event.pathname) AFAICT
        if event.name in self.tempfiles:
            self.tempfiles.pop(event.name)
            logger.info('Sending for processing: %s', event.pathname)
            self.process(event.pathname)


def is_rawfile(filename):
    """Example predicate function for identifying files to process."""
    if '.raw' in filename:
        return True
    return False

def process_rawfile(file_path, output_dir):
    """A data reduction subroutine (specific to user's application)."""
    try:
        #Add a short sleep to demonstrate the parallel nature:
        time.sleep(0.5)
        #Call whatever external processing subroutine you want here
        #We just copy the file in this trivial example.
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        shutil.copyfile(file_path,
                        os.path.join(output_dir, os.path.basename(file_path)))
    # Should always catch *all* exception subclasses here.
    # Otherwise, if an unexpected exception occurs during a pooled process,
    # the file reduction will fail *silently*, and the only clue you'll get
    # will be a missing 'job complete' message.
    except Exception as e:
        error_message = (
            "Hit exception processing file: %s, exception reads:\n%s\n"
                         % (file_path, e))
        return error_message

    return "Successfully processed " + file_path


def processed_callback(summary):
    """Used to log the 'job complete' / error message in the master thread."""
    logger.info('*** Job complete: ' + summary)

def main(options):

    """Define processing logic and fire up the watcher"""
    watch_dir = options.watch_dir
    pool = multiprocessing.Pool(options.nthreads)

    def simply_process_rawfile(file_path):
        """
        Wraps `process_rawfile` to take a single argument (file_path).

        This is the trivial, single threaded version -
        occasionally useful for debugging purposes.
        """
        summary = process_rawfile(file_path, options.output_dir)
        processed_callback(summary)

    def asynchronously_process_rawfile(file_path):
        """
        Wraps `process_rawfile` to take a single argument (file_path).

        This version runs 'process_rawfile' asynchronously via the pool.
        This provides parallel processing, at the cost of being harder to
        debug if anything goes wrong (see notes on exception catching above)
        """
        pool.apply_async(process_rawfile,
             [file_path, options.output_dir],
             callback=processed_callback)

    handler = RsyncNewFileHandler(nthreads=options.nthreads,
                                  file_predicate=is_rawfile,
                                  # file_processor=simply_process_rawfile
                                  file_processor=asynchronously_process_rawfile
                                 )
    wm = pyinotify.WatchManager()
    notifier = pyinotify.Notifier(wm, handler)
    wm.add_watch(options.watch_dir, handler.mask, rec=True)
    log_preamble(options)
    notifier.loop()
    return 0



def log_preamble(options):
    logger.info("***********")
    logger.info('Watching %s', options.watch_dir)
    logger.info('Output dir %s', options.output_dir)
    logger.info('Log dir %s', options.log_dir)
    logger.info("***********")

def setup_logging(options):
    """Set up basic (INFO level) and debug logfiles

    These should list successful reductions, and any errors encountered.
    We also copy the basic log to STDOUT, but it is expected that
    the monitor script will be daemonised / run in a screen in the background.
    """
    if not os.path.isdir(options.log_dir):
        os.makedirs(options.log_dir)
    log_filename = os.path.join(options.log_dir, 'autocruncher_log')
    date_fmt = "%a %d %H:%M:%S"
    std_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s', date_fmt)
    debug_formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s', date_fmt)

    info_logfile = logging.handlers.RotatingFileHandler(log_filename,
                            maxBytes=5e5, backupCount=10)
    info_logfile.setFormatter(std_formatter)
    info_logfile.setLevel(logging.INFO)
    debug_logfile = logging.handlers.RotatingFileHandler(log_filename + '.debug',
                            maxBytes=5e5, backupCount=10)
    debug_logfile.setFormatter(debug_formatter)
    debug_logfile.setLevel(logging.DEBUG)

    log_stream = logging.StreamHandler()
    log_stream.setFormatter(std_formatter)
    log_stream.setLevel(logging.INFO)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(info_logfile)
    logger.addHandler(log_stream)
    logger.addHandler(debug_logfile)

if __name__ == '__main__':
    setup_logging(options)
    sys.exit(main(options))

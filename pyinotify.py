#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# pyinotify.py - python interface to inotify
# Copyright (C) Sébastien Martini <sebastien.martini@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

"""
pyinotify

@author: Sebastien Martini
@license: GPLv2+
@contact: seb@dbzteam.org
"""

class PyinotifyError(Exception):
    """Indicates exceptions raised by a Pyinotify class."""


class UnsupportedPythonVersionError(PyinotifyError):
    """
    Raised for unsupported Python version.
    """
    def __init__(self, version):
        """
        @param version: Current Python version
        @type version: string
        """
        PyinotifyError.__init__(self,
                                ('Python %s is unsupported, requires '
                                'at least Python 2.4') % version)


class UnsupportedLibcVersionError(PyinotifyError):
    """
    Raised for unsupported libc version.
    """
    def __init__(self, version):
        """
        @param version: Current Libc version
        @type version: string
        """
        PyinotifyError.__init__(self,
                                ('Libc %s is unsupported, requires '
                                'at least Libc 2.4') % version)


# Check Python version
import sys
if sys.version < '2.4':
    raise UnsupportedPythonVersionError(sys.version)


# Import directives
import threading
import os
import select
import struct
import fcntl
import errno
import termios
import array
import logging
import atexit
from collections import deque
from datetime import datetime, timedelta
import time
import fnmatch
import re
import ctypes
import ctypes.util
import types

__author__ = "seb@dbzteam.org (Sebastien Martini)"

__version__ = "0.8.6"

__metaclass__ = type  # Use new-style classes by default


# load libc
LIBC = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))

# the libc version > 2.4 check.
# XXX: Maybe it is better to check if the libc has the needed functions inside?
#      Because there are inotify patches for libc 2.3.6.
LIBC.gnu_get_libc_version.restype = ctypes.c_char_p
LIBC_VERSION = LIBC.gnu_get_libc_version()
if (int(LIBC_VERSION.split('.')[0]) < 2 or
    (int(LIBC_VERSION.split('.')[0]) == 2 and
     int(LIBC_VERSION.split('.')[1]) < 4)):
    raise UnsupportedLibcVersionError(LIBC_VERSION)


class PyinotifyLogger(logging.Logger):
    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None,
                   extra=None):
        rv = UnicodeLogRecord(name, level, fn, lno, msg, args, exc_info, func)
        if extra is not None:
            for key in extra:
                if (key in ["message", "asctime"]) or (key in rv.__dict__):
                    raise KeyError("Attempt to overwrite %r in LogRecord" % key)
                rv.__dict__[key] = extra[key]
        return rv


class UnicodeLogRecord(logging.LogRecord):
    def __init__(self, name, level, pathname, lineno,
                 msg, args, exc_info, func=None):
        logging.LogRecord.__init__(self, name, level, pathname, lineno,
                                   msg, args, exc_info, func)

    def getMessage(self):
        msg = self.msg
        if not isinstance(msg, (unicode, str)):
            try:
                msg = str(self.msg)
            except UnicodeError:
                pass
        if self.args:
            if isinstance(self.args, tuple):
                def StrToUnicode(s):
                    if not isinstance(s, str):
                        return s
                    return unicode(s, sys.getfilesystemencoding())
                args = tuple([StrToUnicode(m) for m in self.args])
            else:
                args = self.args
            msg = msg % args
        if not isinstance(msg, unicode):
            msg = unicode(msg, sys.getfilesystemencoding())
        return msg


# logging
logging.setLoggerClass(PyinotifyLogger)
log = logging.getLogger("pyinotify")
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
log.addHandler(console_handler)
log.setLevel(20)


# Try to speed-up execution with psyco
try:
    if False:
        import psyco
        psyco.full()
except ImportError:
    # Cannot import psyco
    pass


### inotify's variables ###


class SysCtlINotify:
    """
    Access (read, write) inotify's variables through sysctl.

    Examples:
      - Read variable: myvar = max_queued_events.value
      - Update variable: max_queued_events.value = 42
    """

    inotify_attrs = {'max_user_instances': 1,
                     'max_user_watches': 2,
                     'max_queued_events': 3}

    def __init__(self, attrname):
        sino = ctypes.c_int * 3
        self._attrname = attrname
        self._attr = sino(5, 20, SysCtlINotify.inotify_attrs[attrname])

    def get_val(self):
        """
        @return: stored value.
        @rtype: int
        """
        oldv = ctypes.c_int(0)
        size = ctypes.c_int(ctypes.sizeof(oldv))
        LIBC.sysctl(self._attr, 3,
                    ctypes.c_voidp(ctypes.addressof(oldv)),
                    ctypes.addressof(size),
                    None, 0)
        return oldv.value

    def set_val(self, nval):
        """
        @param nval: set to nval.
        @type nval: int
        """
        oldv = ctypes.c_int(0)
        sizeo = ctypes.c_int(ctypes.sizeof(oldv))
        newv = ctypes.c_int(nval)
        sizen = ctypes.c_int(ctypes.sizeof(newv))
        LIBC.sysctl(self._attr, 3,
                    ctypes.c_voidp(ctypes.addressof(oldv)),
                    ctypes.addressof(sizeo),
                    ctypes.c_voidp(ctypes.addressof(newv)),
                    ctypes.addressof(sizen))

    value = property(get_val, set_val)

    def __repr__(self):
        return '<%s=%d>' % (self._attrname, self.get_val())


# singleton instances
#
# read int: myvar = max_queued_events.value
# update: max_queued_events.value = 42
#
for attrname in ('max_queued_events', 'max_user_instances', 'max_user_watches'):
    globals()[attrname] = SysCtlINotify(attrname)


# fixme: put those tests elsewhere
#
# print max_queued_events
# print max_queued_events.value
# save = max_queued_events.value
# print save
# max_queued_events.value += 42
# print max_queued_events
# max_queued_events.value = save
# print max_queued_events


### iglob ###


# Code taken from standart Python Lib, slightly modified in order to work
# with pyinotify (don't exclude dotted files/dirs like .foo).
# Original version:
# @see: http://svn.python.org/projects/python/trunk/Lib/glob.py

def iglob(pathname):
    if not has_magic(pathname):
        if hasattr(os.path, 'lexists'):
            if os.path.lexists(pathname):
                yield pathname
        else:
            if os.path.islink(pathname) or os.path.exists(pathname):
                yield pathname
        return
    dirname, basename = os.path.split(pathname)
    # relative pathname
    if not dirname:
        return
    # absolute pathname
    if has_magic(dirname):
        dirs = iglob(dirname)
    else:
        dirs = [dirname]
    if has_magic(basename):
        glob_in_dir = glob1
    else:
        glob_in_dir = glob0
    for dirname in dirs:
        for name in glob_in_dir(dirname, basename):
            yield os.path.join(dirname, name)

def glob1(dirname, pattern):
    if not dirname:
        dirname = os.curdir
    try:
        names = os.listdir(dirname)
    except os.error:
        return []
    return fnmatch.filter(names, pattern)

def glob0(dirname, basename):
    if basename == '' and os.path.isdir(dirname):
        # `os.path.split()` returns an empty basename for paths ending with a
        # directory separator.  'q*x/' should match only directories.
        return [basename]
    if hasattr(os.path, 'lexists'):
        if os.path.lexists(os.path.join(dirname, basename)):
            return [basename]
    else:
        if (os.path.islink(os.path.join(dirname, basename)) or
            os.path.exists(os.path.join(dirname, basename))):
            return [basename]
    return []

magic_check = re.compile('[*?[]')

def has_magic(s):
    return magic_check.search(s) is not None



### Core ###


class EventsCodes:
    """
    Set of codes corresponding to each kind of events.
    Some of these flags are used to communicate with inotify, whereas
    the others are sent to userspace by inotify notifying some events.

    @cvar IN_ACCESS: File was accessed.
    @type IN_ACCESS: int
    @cvar IN_MODIFY: File was modified.
    @type IN_MODIFY: int
    @cvar IN_ATTRIB: Metadata changed.
    @type IN_ATTRIB: int
    @cvar IN_CLOSE_WRITE: Writtable file was closed.
    @type IN_CLOSE_WRITE: int
    @cvar IN_CLOSE_NOWRITE: Unwrittable file closed.
    @type IN_CLOSE_NOWRITE: int
    @cvar IN_OPEN: File was opened.
    @type IN_OPEN: int
    @cvar IN_MOVED_FROM: File was moved from X.
    @type IN_MOVED_FROM: int
    @cvar IN_MOVED_TO: File was moved to Y.
    @type IN_MOVED_TO: int
    @cvar IN_CREATE: Subfile was created.
    @type IN_CREATE: int
    @cvar IN_DELETE: Subfile was deleted.
    @type IN_DELETE: int
    @cvar IN_DELETE_SELF: Self (watched item itself) was deleted.
    @type IN_DELETE_SELF: int
    @cvar IN_MOVE_SELF: Self (watched item itself) was moved.
    @type IN_MOVE_SELF: int
    @cvar IN_UNMOUNT: Backing fs was unmounted.
    @type IN_UNMOUNT: int
    @cvar IN_Q_OVERFLOW: Event queued overflowed.
    @type IN_Q_OVERFLOW: int
    @cvar IN_IGNORED: File was ignored.
    @type IN_IGNORED: int
    @cvar IN_ONLYDIR: only watch the path if it is a directory (new
                      in kernel 2.6.15).
    @type IN_ONLYDIR: int
    @cvar IN_DONT_FOLLOW: don't follow a symlink (new in kernel 2.6.15).
                          IN_ONLYDIR we can make sure that we don't watch
                          the target of symlinks.
    @type IN_DONT_FOLLOW: int
    @cvar IN_MASK_ADD: add to the mask of an already existing watch (new
                       in kernel 2.6.14).
    @type IN_MASK_ADD: int
    @cvar IN_ISDIR: Event occurred against dir.
    @type IN_ISDIR: int
    @cvar IN_ONESHOT: Only send event once.
    @type IN_ONESHOT: int
    @cvar ALL_EVENTS: Alias for considering all of the events.
    @type ALL_EVENTS: int
    """

    # The idea here is 'configuration-as-code' - this way, we get our nice class
    # constants, but we also get nice human-friendly text mappings to do lookups
    # against as well, for free:
    FLAG_COLLECTIONS = {'OP_FLAGS': {
        'IN_ACCESS'        : 0x00000001,  # File was accessed
        'IN_MODIFY'        : 0x00000002,  # File was modified
        'IN_ATTRIB'        : 0x00000004,  # Metadata changed
        'IN_CLOSE_WRITE'   : 0x00000008,  # Writable file was closed
        'IN_CLOSE_NOWRITE' : 0x00000010,  # Unwritable file closed
        'IN_OPEN'          : 0x00000020,  # File was opened
        'IN_MOVED_FROM'    : 0x00000040,  # File was moved from X
        'IN_MOVED_TO'      : 0x00000080,  # File was moved to Y
        'IN_CREATE'        : 0x00000100,  # Subfile was created
        'IN_DELETE'        : 0x00000200,  # Subfile was deleted
        'IN_DELETE_SELF'   : 0x00000400,  # Self (watched item itself)
                                          # was deleted
        'IN_MOVE_SELF'     : 0x00000800,  # Self (watched item itself) was moved
        },
                        'EVENT_FLAGS': {
        'IN_UNMOUNT'       : 0x00002000,  # Backing fs was unmounted
        'IN_Q_OVERFLOW'    : 0x00004000,  # Event queued overflowed
        'IN_IGNORED'       : 0x00008000,  # File was ignored
        },
                        'SPECIAL_FLAGS': {
        'IN_ONLYDIR'       : 0x01000000,  # only watch the path if it is a
                                          # directory
        'IN_DONT_FOLLOW'   : 0x02000000,  # don't follow a symlink
        'IN_MASK_ADD'      : 0x20000000,  # add to the mask of an already
                                          # existing watch
        'IN_ISDIR'         : 0x40000000,  # event occurred against dir
        'IN_ONESHOT'       : 0x80000000,  # only send event once
        },
                        }

    def maskname(mask):
        """
        Return the event name associated to mask. IN_ISDIR is appended when
        appropriate. Note: only one event is returned, because only one is
        raised once at a time.

        @param mask: mask.
        @type mask: int
        @return: event name.
        @rtype: str
        """
        ms = mask
        name = '%s'
        if mask & IN_ISDIR:
            ms = mask - IN_ISDIR
            name = '%s|IN_ISDIR'
        return name % EventsCodes.ALL_VALUES[ms]

    maskname = staticmethod(maskname)


# So let's now turn the configuration into code
EventsCodes.ALL_FLAGS = {}
EventsCodes.ALL_VALUES = {}
for flagc, valc in EventsCodes.FLAG_COLLECTIONS.iteritems():
    # Make the collections' members directly accessible through the
    # class dictionary
    setattr(EventsCodes, flagc, valc)

    # Collect all the flags under a common umbrella
    EventsCodes.ALL_FLAGS.update(valc)

    # Make the individual masks accessible as 'constants' at globals() scope
    # and masknames accessible by values.
    for name, val in valc.iteritems():
        globals()[name] = val
        EventsCodes.ALL_VALUES[val] = name


# all 'normal' events
ALL_EVENTS = reduce(lambda x, y: x | y, EventsCodes.OP_FLAGS.itervalues())
EventsCodes.ALL_FLAGS['ALL_EVENTS'] = ALL_EVENTS
EventsCodes.ALL_VALUES[ALL_EVENTS] = 'ALL_EVENTS'


class _Event:
    """
    Event structure, represent events raised by the system. This
    is the base class and should be subclassed.

    """
    def __init__(self, dict_):
        """
        Attach attributes (contained in dict_) to self.
        """
        for tpl in dict_.iteritems():
            setattr(self, *tpl)

    def __repr__(self):
        """
        @return: String representation.
        @rtype: str
        """
        s = ''
        for attr, value in sorted(self.__dict__.items(), key=lambda x: x[0]):
            if attr.startswith('_'):
                continue
            if attr == 'mask':
                value = hex(getattr(self, attr))
            elif isinstance(value, basestring) and not value:
                value ="''"
            s += ' %s%s%s' % (Color.FieldName(attr),
                              Color.Punctuation('='),
                              Color.FieldValue(value))

        s = '%s%s%s %s' % (Color.Punctuation('<'),
                           Color.ClassName(self.__class__.__name__),
                           s,
                           Color.Punctuation('>'))
        return s


class _RawEvent(_Event):
    """
    Raw event, it contains only the informations provided by the system.
    It doesn't infer anything.
    """
    def __init__(self, wd, mask, cookie, name):
        """
        @param wd: Watch Descriptor.
        @type wd: int
        @param mask: Bitmask of events.
        @type mask: int
        @param cookie: Cookie.
        @type cookie: int
        @param name: Basename of the file or directory against which the
                     event was raised, in case where the watched directory
                     is the parent directory. None if the event was raised
                     on the watched item itself.
        @type name: string or None
        """
        # name: remove trailing '\0'
        super(_RawEvent, self).__init__({'wd': wd,
                                         'mask': mask,
                                         'cookie': cookie,
                                         'name': name.rstrip('\0')})
        log.debug(repr(self))


class Event(_Event):
    """
    This class contains all the useful informations about the observed
    event. However, the incorporation of each field is not guaranteed and
    depends on the type of event. In effect, some fields are irrelevant
    for some kind of event (for example 'cookie' is meaningless for
    IN_CREATE whereas it is useful for IN_MOVE_TO).

    The possible fields are:
      - wd (int): Watch Descriptor.
      - mask (int): Mask.
      - maskname (str): Readable event name.
      - path (str): path of the file or directory being watched.
      - name (str): Basename of the file or directory against which the
              event was raised, in case where the watched directory
              is the parent directory. None if the event was raised
              on the watched item itself. This field is always provided
              even if the string is ''.
      - pathname (str): absolute path of: path + name
      - cookie (int): Cookie.
      - dir (bool): is the event raised against directory.

    """
    def __init__(self, raw):
        """
        Concretely, this is the raw event plus inferred infos.
        """
        _Event.__init__(self, raw)
        self.maskname = EventsCodes.maskname(self.mask)
        try:
            if self.name:
                self.pathname = os.path.abspath(os.path.join(self.path,
                                                             self.name))
            else:
                self.pathname = os.path.abspath(self.path)
        except AttributeError:
            pass


class ProcessEventError(PyinotifyError):
    """
    ProcessEventError Exception. Raised on ProcessEvent error.
    """
    def __init__(self, err):
        """
        @param err: Exception error description.
        @type err: string
        """
        PyinotifyError.__init__(self, err)


class _ProcessEvent:
    """
    Abstract processing event class.
    """
    def __call__(self, event):
        """
        To behave like a functor the object must be callable.
        This method is a dispatch method. Lookup order:
          1. process_MASKNAME method
          2. process_FAMILY_NAME method
          3. otherwise call process_default

        @param event: Event to be processed.
        @type event: Event object
        @return: By convention when used from the ProcessEvent class:
                 - Returning False or None (default value) means keep on
                 executing next chained functors (see chain.py example).
                 - Returning True instead means do not execute next
                   processing functions.
        @rtype: bool
        @raise ProcessEventError: Event object undispatchable,
                                  unknown event.
        """
        stripped_mask = event.mask - (event.mask & IN_ISDIR)
        maskname = EventsCodes.ALL_VALUES.get(stripped_mask)
        if maskname is None:
            raise ProcessEventError("Unknown mask 0x%08x" % stripped_mask)

        # 1- look for process_MASKNAME
        meth = getattr(self, 'process_' + maskname, None)
        if meth is not None:
            return meth(event)
        # 2- look for process_FAMILY_NAME
        meth = getattr(self, 'process_IN_' + maskname.split('_')[1], None)
        if meth is not None:
            return meth(event)
        # 3- default call method process_default
        return self.process_default(event)

    def __repr__(self):
        return '<%s>' % self.__class__.__name__


class _SysProcessEvent(_ProcessEvent):
    """
    There is three kind of processing according to each event:

      1. special handling (deletion from internal container, bug, ...).
      2. default treatment: which is applied to most of events.
      4. IN_ISDIR is never sent alone, he is piggybacked with a standart
         event, he is not processed as the others events, instead, its
         value is captured and appropriately aggregated to dst event.
    """
    def __init__(self, wm, notifier):
        """

        @param wm: Watch Manager.
        @type wm: WatchManager instance
        @param notifier: notifier.
        @type notifier: Instance of Notifier.
        """
        self._watch_manager = wm  # watch manager
        self._notifier = notifier  # notifier
        self._mv_cookie = {}  # {cookie(int): (src_path(str), date), ...}
        self._mv = {}  # {src_path(str): (dst_path(str), date), ...}

    def cleanup(self):
        """
        Cleanup (delete) old (>1mn) records contained in self._mv_cookie
        and self._mv.
        """
        date_cur_ = datetime.now()
        for seq in [self._mv_cookie, self._mv]:
            for k in seq.keys():
               if (date_cur_ - seq[k][1]) > timedelta(minutes=1):
                   log.debug('cleanup: deleting entry %s', seq[k][0])
                   del seq[k]

    def process_IN_CREATE(self, raw_event):
        """
        If the event concerns a directory and the auto_add flag of the
        targetted watch is set to True, a new watch is added on this
        new directory, with the same attributes's values than those of
        this watch.
        """
        if raw_event.mask & IN_ISDIR:
            watch_ = self._watch_manager._wmd.get(raw_event.wd)
            if watch_.auto_add:
                addw = self._watch_manager.add_watch
                newwd = addw(os.path.join(watch_.path, raw_event.name),
                             watch_.mask, proc_fun=watch_.proc_fun,
                             rec=False, auto_add=watch_.auto_add)

                # Trick to handle mkdir -p /t1/t2/t3 where t1 is watched and
                # t2 and t3 are created.
                # Since the directory is new, then everything inside it
                # must also be new.
                base = os.path.join(watch_.path, raw_event.name)
                if newwd[base] > 0:
                    for name in os.listdir(base):
                        inner = os.path.join(base, name)
                        if (os.path.isdir(inner) and
                            self._watch_manager.get_wd(inner) is None):
                            # Generate (simulate) creation event for sub
                            # directories.
                            rawevent = _RawEvent(newwd[base],
                                                 IN_CREATE | IN_ISDIR,
                                                 0, name)
                            self._notifier._eventq.append(rawevent)
        return self.process_default(raw_event)

    def process_IN_MOVED_FROM(self, raw_event):
        """
        Map the cookie with the source path (+ date for cleaning).
        """
        watch_ = self._watch_manager._wmd.get(raw_event.wd)
        path_ = watch_.path
        src_path = os.path.normpath(os.path.join(path_, raw_event.name))
        self._mv_cookie[raw_event.cookie] = (src_path, datetime.now())
        return self.process_default(raw_event, {'cookie': raw_event.cookie})

    def process_IN_MOVED_TO(self, raw_event):
        """
        Map the source path with the destination path (+ date for
        cleaning).
        """
        watch_ = self._watch_manager._wmd.get(raw_event.wd)
        path_ = watch_.path
        dst_path = os.path.normpath(os.path.join(path_, raw_event.name))
        mv_ = self._mv_cookie.get(raw_event.cookie)
        if mv_:
            self._mv[mv_[0]] = (dst_path, datetime.now())
        return self.process_default(raw_event, {'cookie': raw_event.cookie})

    def process_IN_MOVE_SELF(self, raw_event):
        """
        STATUS: the following bug has been fixed in the recent kernels (fixme:
        which version ?). Now it raises IN_DELETE_SELF instead.

        Old kernels are bugged, this event is raised when the watched item
        was moved, so we must update its path, but under some circumstances it
        can be impossible: if its parent directory and its destination
        directory aren't watched. The kernel (see include/linux/fsnotify.h)
        doesn't bring us enough informations like the destination path of
        moved items.
        """
        watch_ = self._watch_manager._wmd.get(raw_event.wd)
        src_path = watch_.path
        mv_ = self._mv.get(src_path)
        if mv_:
            watch_.path = mv_[0]
        else:
            log.error("The path %s of this watch %s is not reliable anymore",
                      watch_.path, watch_)
            if not watch_.path.endswith('-wrong-path'):
                watch_.path += '-wrong-path'
        # FIXME: should we pass the cookie even if this is not standart?
        return self.process_default(raw_event)

    def process_IN_Q_OVERFLOW(self, raw_event):
        """
        Only signal overflow, most of the common flags are irrelevant
        for this event (path, wd, name).
        """
        return Event({'mask': raw_event.mask})

    def process_IN_IGNORED(self, raw_event):
        """
        The watch descriptor raised by this event is now ignored (forever),
        it can be safely deleted from watch manager dictionary.
        After this event we can be sure that neither the event queue
        neither the system will raise an event associated to this wd.
        """
        event_ = self.process_default(raw_event)
        try:
            del self._watch_manager._wmd[raw_event.wd]
        except KeyError, err:
            log.error(str(err))
        return event_

    def process_default(self, raw_event, to_append={}):
        """
        Common handling for the following events:

        IN_ACCESS, IN_MODIFY, IN_ATTRIB, IN_CLOSE_WRITE, IN_CLOSE_NOWRITE,
        IN_OPEN, IN_DELETE, IN_DELETE_SELF, IN_UNMOUNT.
        """
        ret = None
        watch_ = self._watch_manager._wmd.get(raw_event.wd)
        if raw_event.mask & (IN_DELETE_SELF | IN_MOVE_SELF):
            # unfornately information not provided by the kernel
            dir_ = watch_.dir
        else:
            dir_ = bool(raw_event.mask & IN_ISDIR)
        dict_ = {'wd': raw_event.wd,
                 'mask': raw_event.mask,
                 'path': watch_.path,
                 'name': raw_event.name,
                 'dir': dir_}
        dict_.update(to_append)
        return Event(dict_)


class ProcessEvent(_ProcessEvent):
    """
    Process events objects, can be specialized via subclassing, thus its
    behavior can be overriden:

    Note: you should not override __init__ in your subclass instead define
    a my_init() method, this method will be called from the constructor of
    this class with optional parameters.

      1. Provide methods, e.g. process_IN_DELETE for processing a given kind
         of event (eg. IN_DELETE in this case).
      2. Or/and provide methods for processing events by 'family', e.g.
         process_IN_CLOSE method will process both IN_CLOSE_WRITE and
         IN_CLOSE_NOWRITE events (if process_IN_CLOSE_WRITE and
         process_IN_CLOSE_NOWRITE aren't defined).
      3. Or/and override process_default for processing the remaining kind of
         events.
    """
    pevent = None

    def __init__(self, pevent=None, **kargs):
        """
        Enable chaining of ProcessEvent instances.

        @param pevent: optional callable object, will be called on event
                       processing (before self).
        @type pevent: callable
        @param kargs: optional arguments delagated to template method my_init
        @type kargs: dict
        """
        self.pevent = pevent
        self.my_init(**kargs)

    def my_init(self, **kargs):
        """
        Override this method when subclassing if you want to achieve
        custom initialization of your subclass' instance. You MUST pass
        keyword arguments. This method does nothing by default.

        @param kargs: optional arguments delagated to template method my_init
        @type kargs: dict
        """
        pass

    def __call__(self, event):
        stop_chaining = False
        if self.pevent is not None:
            # By default methods return None so we fix as guideline
            # that methods asking for stop chaining must explicitely
            # return non None or False values, otherwise the default
            # behavior is to chain call to the corresponding local
            # method.
            stop_chaining = self.pevent(event)
        if not stop_chaining:
            return _ProcessEvent.__call__(self, event)

    def nested_pevent(self):
        return self.pevent

    def process_default(self, event):
        """
        Default default processing event method. Print event
        on standart output.

        @param event: Event to be processed.
        @type event: Event instance
        """
        print(repr(event))


class ChainIfTrue(ProcessEvent):
    """
    Makes conditional chaining depending on the result of the nested
    processing instance.
    """
    def my_init(self, func):
        self._func = func

    def process_default(self, event):
        return not self._func(event)


class Stats(ProcessEvent):
    def my_init(self):
        self._start_time = time.time()
        self._stats = {}
        self._stats_lock = threading.Lock()

    def process_default(self, event):
        self._stats_lock.acquire()
        try:
            events = event.maskname.split('|')
            for event_name in events:
                count = self._stats.get(event_name, 0)
                self._stats[event_name] = count + 1
        finally:
            self._stats_lock.release()

    def _stats_copy(self):
        self._stats_lock.acquire()
        try:
            return self._stats.copy()
        finally:
            self._stats_lock.release()

    def __repr__(self):
        stats = self._stats_copy()

        t = int(time.time() - self._start_time)
        if t < 60:
            ts = str(t) + 'sec'
        elif 60 <= t < 3600:
            ts = '%dmn%dsec' % (t / 60, t % 60)
        elif 3600 <= t < 86400:
            ts = '%dh%dmn' % (t / 3600, (t % 3600) / 60)
        elif t >= 86400:
            ts = '%dd%dh' % (t / 86400, (t % 86400) / 3600)
        stats['ElapsedTime'] = ts

        l = []
        for ev, value in sorted(stats.items(), key=lambda x: x[0]):
            l.append(' %s=%s' % (Color.FieldName(ev),
                                 Color.FieldValue(value)))
        s = '<%s%s >' % (Color.ClassName(self.__class__.__name__),
                         ''.join(l))
        return s

    def dump(self, filename):
        fo = file(filename, 'wb')
        try:
            fo.write(str(self))
        finally:
            fo.close()

    def __str__(self, scale=45):
        stats = self._stats_copy()
        if not stats:
            return ''

        m = max(stats.values())
        unity = int(round(float(m) / scale)) or 1
        fmt = '%%-26s%%-%ds%%s' % (len(Color.FieldValue('@' * scale))
                                   + 1)
        def func(x):
            return fmt % (Color.FieldName(x[0]),
                          Color.FieldValue('@' * (x[1] / unity)),
                          Color.Simple('%d' % x[1], 'yellow'))
        s = '\n'.join(map(func, sorted(stats.items(), key=lambda x: x[0])))
        return s


class NotifierError(PyinotifyError):
    """
    Notifier Exception. Raised on Notifier error.

    """
    def __init__(self, err):
        """
        @param err: Exception string's description.
        @type err: string
        """
        PyinotifyError.__init__(self, err)


class Notifier:
    """
    Read notifications, process events.

    """
    def __init__(self, watch_manager, default_proc_fun=ProcessEvent(),
                 read_freq=0, treshold=0, timeout=None):
        """
        Initialization. read_freq, treshold and timeout parameters are used
        when looping.

        @param watch_manager: Watch Manager.
        @type watch_manager: WatchManager instance
        @param default_proc_fun: Default processing method.
        @type default_proc_fun: instance of ProcessEvent
        @param read_freq: if read_freq == 0, events are read asap,
                          if read_freq is > 0, this thread sleeps
                          max(0, read_freq - timeout) seconds. But if
                          timeout is None it can be different because
                          poll is blocking waiting for something to read.
        @type read_freq: int
        @param treshold: File descriptor will be read only if its size to
                         read is >= treshold. If != 0, you likely want to
                         use it in combination with read_freq because
                         without that you keep looping without really reading
                         anything and that until the amount to read
                         is >= treshold. At least with read_freq you may sleep.
        @type treshold: int
        @param timeout:
            http://docs.python.org/lib/poll-objects.html#poll-objects
        @type timeout: int
        """
        # watch manager instance
        self._watch_manager = watch_manager
        # file descriptor
        self._fd = self._watch_manager._fd
        # poll object and registration
        self._pollobj = select.poll()
        self._pollobj.register(self._fd, select.POLLIN)
        # This pipe is correctely initialized and used by ThreadedNotifier
        self._pipe = (-1, -1)
        # event queue
        self._eventq = deque()
        # system processing functor, common to all events
        self._sys_proc_fun = _SysProcessEvent(self._watch_manager, self)
        # default processing method
        self._default_proc_fun = default_proc_fun
        # loop parameters
        self._read_freq = read_freq
        self._treshold = treshold
        self._timeout = timeout

    def proc_fun(self):
        return self._default_proc_fun

    def check_events(self):
        """
        Check for new events available to read, blocks up to timeout
        milliseconds.

        @return: New events to read.
        @rtype: bool
        """
        while True:
            try:
                # blocks up to 'timeout' milliseconds
                ret = self._pollobj.poll(self._timeout)
            except select.error, err:
                if err[0] == errno.EINTR:
                    continue # interrupted, retry
                else:
                    raise
            else:
                break

        if not ret or (self._pipe[0] == ret[0][0]):
            return False
        # only one fd is polled
        return ret[0][1] & select.POLLIN

    def read_events(self):
        """
        Read events from device, build _RawEvents, and enqueue them.
        """
        buf_ = array.array('i', [0])
        # get event queue size
        if fcntl.ioctl(self._fd, termios.FIONREAD, buf_, 1) == -1:
            return
        queue_size = buf_[0]
        if queue_size < self._treshold:
            log.debug('(fd: %d) %d bytes available to read but treshold is '
                      'fixed to %d bytes', self._fd, queue_size, self._treshold)
            return

        try:
            # read content from file
            r = os.read(self._fd, queue_size)
        except Exception, msg:
            raise NotifierError(msg)
        log.debug('event queue size: %d', queue_size)
        rsum = 0  # counter
        while rsum < queue_size:
            s_size = 16
            # retrieve wd, mask, cookie
            s_ = struct.unpack('iIII', r[rsum:rsum+s_size])
            # length of name
            fname_len = s_[3]
            # field 'length' useless
            s_ = s_[:-1]
            # retrieve name
            s_ += struct.unpack('%ds' % fname_len,
                                r[rsum + s_size:rsum + s_size + fname_len])
            self._eventq.append(_RawEvent(*s_))
            rsum += s_size + fname_len

    def process_events(self):
        """
        Routine for processing events from queue by calling their
        associated proccessing function (instance of ProcessEvent).
        It also do internal processings, to keep the system updated.
        """
        while self._eventq:
            raw_event = self._eventq.popleft()  # pop next event
            watch_ = self._watch_manager._wmd.get(raw_event.wd)
            revent = self._sys_proc_fun(raw_event)  # system processings
            if watch_ and watch_.proc_fun:
                watch_.proc_fun(revent)  # user processings
            else:
                self._default_proc_fun(revent)
        self._sys_proc_fun.cleanup()  # remove olds MOVED_* events records


    def __daemonize(self, pid_file=None, force_kill=False, stdin=os.devnull,
                    stdout=os.devnull, stderr=os.devnull):
        """
        pid_file: file to which pid will be written.
        force_kill: if True kill the process associated to pid_file.
        stdin, stdout, stderr: files associated to common streams.
        """
        if pid_file is None:
            dirname = '/var/run/'
            basename = sys.argv[0] or 'pyinotify'
            pid_file = os.path.join(dirname, basename + '.pid')

        if os.path.exists(pid_file):
            fo = file(pid_file, 'rb')
            try:
                try:
                    pid = int(fo.read())
                except ValueError:
                    pid = None
                if pid is not None:
                    try:
                        os.kill(pid, 0)
                    except OSError, err:
                        pass
                    else:
                        if not force_kill:
                            s = 'There is already a pid file %s with pid %d'
                            raise NotifierError(s % (pid_file, pid))
                        else:
                            os.kill(pid, 9)
            finally:
                fo.close()


        def fork_daemon():
            # Adapted from Chad J. Schroeder's recipe
            pid = os.fork()
            if (pid == 0):
                # parent 2
                os.setsid()
                pid = os.fork()
                if (pid == 0):
                    # child
                    os.chdir('/')
                    os.umask(0)
                else:
                    # parent 2
                    os._exit(0)
            else:
                # parent 1
                os._exit(0)

            fd_inp = os.open(stdin, os.O_RDONLY)
            os.dup2(fd_inp, 0)
            fd_out = os.open(stdout, os.O_WRONLY|os.O_CREAT)
            os.dup2(fd_out, 1)
            fd_err = os.open(stderr, os.O_WRONLY|os.O_CREAT)
            os.dup2(fd_err, 2)

        # Detach task
        fork_daemon()

        # Write pid
        fo = file(pid_file, 'wb')
        try:
            fo.write(str(os.getpid()) + '\n')
        finally:
            fo.close()

        atexit.register(lambda : os.unlink(pid_file))


    def _sleep(self, ref_time):
        # Only consider sleeping if read_freq is > 0
        if self._read_freq > 0:
            cur_time = time.time()
            sleep_amount = self._read_freq - (cur_time - ref_time)
            if sleep_amount > 0:
                log.debug('Now sleeping %d seconds', sleep_amount)
                time.sleep(sleep_amount)


    def loop(self, callback=None, daemonize=False, **args):
        """
        Events are read only once time every min(read_freq, timeout)
        seconds at best and only if the size to read is >= treshold.

        @param callback: Functor called after each event processing. Expects
                         to receive notifier object (self) as first parameter.
        @type callback: callable
        @param daemonize: This thread is daemonized if set to True.
        @type daemonize: boolean
        """
        if daemonize:
            self.__daemonize(**args)

        # Read and process events forever
        while 1:
            try:
                self.process_events()
                if callback is not None:
                    callback(self)
                ref_time = time.time()
                # check_events is blocking
                if self.check_events():
                    self._sleep(ref_time)
                    self.read_events()
            except KeyboardInterrupt:
                # Unless sigint is caught (Control-C)
                log.debug('Pyinotify stops monitoring.')
                # Stop monitoring
                self.stop()
                break

    def stop(self):
        """
        Close the inotify's instance (close its file descriptor).
        It destroys all existing watches, pending events,...
        """
        self._pollobj.unregister(self._fd)
        os.close(self._fd)


class ThreadedNotifier(threading.Thread, Notifier):
    """
    This notifier inherits from threading.Thread for instantiating a separate
    thread, and also inherits from Notifier, because it is a threaded notifier.

    Note that everything possible with this class is also possible through
    Notifier. Moreover Notifier is _better_ under many aspects: not threaded,
    can be easily daemonized.
    """
    def __init__(self, watch_manager, default_proc_fun=ProcessEvent(),
                 read_freq=0, treshold=0, timeout=None):
        """
        Initialization, initialize base classes. read_freq, treshold and
        timeout parameters are used when looping.

        @param watch_manager: Watch Manager.
        @type watch_manager: WatchManager instance
        @param default_proc_fun: Default processing method.
        @type default_proc_fun: instance of ProcessEvent
        @param read_freq: if read_freq == 0, events are read asap,
                          if read_freq is > 0, this thread sleeps
                          max(0, read_freq - timeout) seconds.
        @type read_freq: int
        @param treshold: File descriptor will be read only if its size to
                         read is >= treshold. If != 0, you likely want to
                         use it in combination with read_freq because
                         without that you keep looping without really reading
                         anything and that until the amount to read
                         is >= treshold. At least with read_freq you may sleep.
        @type treshold: int
        @param timeout:
           see http://docs.python.org/lib/poll-objects.html#poll-objects
           Read the corresponding comment in the source code before changing
           it.
        @type timeout: int
        """
        # Init threading base class
        threading.Thread.__init__(self)
        # Stop condition
        self._stop_event = threading.Event()
        # Init Notifier base class
        Notifier.__init__(self, watch_manager, default_proc_fun, read_freq,
                          treshold, timeout)
        # Create a new pipe used for thread termination
        self._pipe = os.pipe()
        self._pollobj.register(self._pipe[0], select.POLLIN)

    def stop(self):
        """
        Stop the notifier's loop. Stop notification. Join the thread.
        """
        self._stop_event.set()
        os.write(self._pipe[1], 'stop')
        threading.Thread.join(self)
        Notifier.stop(self)
        self._pollobj.unregister(self._pipe[0])
        os.close(self._pipe[0])
        os.close(self._pipe[1])

    def loop(self):
        """
        Thread's main loop. Don't meant to be called by user directly.
        Call start() instead.

        Events are read only once time every min(read_freq, timeout)
        seconds at best and only if the size of events to read is >= treshold.
        """
        # When the loop must be terminated .stop() is called, 'stop'
        # is written to pipe fd so poll() returns and .check_events()
        # returns False which make evaluate the While's stop condition
        # ._stop_event.isSet() wich put an end to the thread's execution.
        while not self._stop_event.isSet():
            self.process_events()
            ref_time = time.time()
            if self.check_events():
                self._sleep(ref_time)
                self.read_events()

    def run(self):
        """
        Start the thread's loop: read and process events until the method
        stop() is called.
        Never call this method directly, instead call the start() method
        inherited from threading.Thread, which then will call run().
        """
        self.loop()


class Watch:
    """
    Represent a watch, i.e. a file or directory being watched.

    """
    def __init__(self, **keys):
        """
        Initializations.

        @param wd: Watch descriptor.
        @type wd: int
        @param path: Path of the file or directory being watched.
        @type path: str
        @param mask: Mask.
        @type mask: int
        @param proc_fun: Processing callable object.
        @type proc_fun:
        @param auto_add: Automatically add watches on new directories.
        @type auto_add: bool
        """
        for k, v in keys.iteritems():
            setattr(self, k, v)
        self.dir = os.path.isdir(self.path)

    def __repr__(self):
        """
        @return: String representation.
        @rtype: str
        """
        s = ' '.join(['%s%s%s' % (Color.FieldName(attr),
                                  Color.Punctuation('='),
                                  Color.FieldValue(getattr(self, attr))) \
                      for attr in self.__dict__ if not attr.startswith('_')])

        s = '%s%s %s %s' % (Color.Punctuation('<'),
                            Color.ClassName(self.__class__.__name__),
                            s,
                            Color.Punctuation('>'))
        return s


class ExcludeFilter:
    """
    ExcludeFilter is an exclusion filter.
    """

    def __init__(self, arg_lst):
        """
        @param arg_lst: is either a list or dict of patterns:
                        [pattern1, ..., patternn]
                        {'filename1': (list1, listn), ...} where list1 is
                        a list of patterns
        @type arg_lst: list or dict
        """
        if isinstance(arg_lst, dict):
            lst = self._load_patterns(arg_lst)
        elif isinstance(arg_lst, list):
            lst = arg_lst
        else:
            raise TypeError

        self._lregex = []
        for regex in lst:
            self._lregex.append(re.compile(regex, re.UNICODE))

    def _load_patterns(self, dct):
        lst = []
        for path, varnames in dct.iteritems():
            loc = {}
            execfile(path, {}, loc)
            for varname in varnames:
                lst.extend(loc.get(varname, []))
        return lst

    def _match(self, regex, path):
        return regex.match(path) is not None

    def __call__(self, path):
        """
        @param path: path to match against regexps.
        @type path: str
        @return: return True is path has been matched and should
                 be excluded, False otherwise.
        @rtype: bool
        """
        for regex in self._lregex:
            if self._match(regex, path):
                return True
        return False


class WatchManagerError(Exception):
    """
    WatchManager Exception. Raised on error encountered on watches
    operations.

    """
    def __init__(self, msg, wmd):
        """
        @param msg: Exception string's description.
        @type msg: string
        @param wmd: This dictionary contains the wd assigned to paths of the
                    same call for which watches were successfully added.
        @type wmd: dict
        """
        self.wmd = wmd
        Exception.__init__(self, msg)


class WatchManager:
    """
    Provide operations for watching files and directories. Integrated
    dictionary is used to reference watched items.
    """
    def __init__(self, exclude_filter=lambda path: False):
        """
        Initialization: init inotify, init watch manager dictionary.
        Raise OSError if initialization fails.

        @param exclude_filter: boolean function, returns True if current
                               path must be excluded from being watched.
                               Convenient for providing a common exclusion
                               filter for every call to add_watch.
        @type exclude_filter: bool
        """
        self._exclude_filter = exclude_filter
        self._wmd = {}  # watch dict key: watch descriptor, value: watch
        self._fd = LIBC.inotify_init() # inotify's init, file descriptor
        if self._fd < 0:
            raise OSError()

    def __add_watch(self, path, mask, proc_fun, auto_add):
        """
        Add a watch on path, build a Watch object and insert it in the
        watch manager dictionary. Return the wd value.
        """
        # Unicode strings are converted to bytes strings, it seems to be
        # required because LIBC.inotify_add_watch does not work well when
        # it receives an ctypes.create_unicode_buffer instance as argument.
        # Therefore even wd are indexed with bytes string and not with
        # unicode paths.
        if isinstance(path, unicode):
            byte_path = path.encode(sys.getfilesystemencoding())
        else:
            byte_path = path

        wd_ = LIBC.inotify_add_watch(self._fd,
                                     ctypes.create_string_buffer(byte_path),
                                     mask)
        if wd_ < 0:
            return wd_
        watch_ = Watch(wd=wd_, path=os.path.normpath(byte_path), mask=mask,
                       proc_fun=proc_fun, auto_add=auto_add)
        self._wmd[wd_] = watch_
        log.debug('New %s', watch_)
        return wd_

    def __glob(self, path, do_glob):
        if do_glob:
            return iglob(path)
        else:
            return [path]

    def add_watch(self, path, mask, proc_fun=None, rec=False,
                  auto_add=False, do_glob=False, quiet=True,
                  exclude_filter=None):
        """
        Add watch(s) on given path(s) with the specified mask and
        optionnally with a processing function and recursive flag.

        @param path: Path to watch, the path can either be a file or a
                     directory. Also accepts a sequence (list) of paths.
        @type path: string or list of string
        @param mask: Bitmask of events.
        @type mask: int
        @param proc_fun: Processing object.
        @type proc_fun: function or ProcessEvent instance or instance of
                        one of its subclasses or callable object.
        @param rec: Recursively add watches from path on all its
                    subdirectories, set to False by default (doesn't
                    follows symlinks).
        @type rec: bool
        @param auto_add: Automatically add watches on newly created
                         directories in the watch's path.
        @type auto_add: bool
        @param do_glob: Do globbing on pathname.
        @type do_glob: bool
        @param quiet: if False raises a WatchManagerError exception on
                      error. See example not_quiet.py
        @type quiet: bool
        @param exclude_filter: boolean function, returns True if current
                               path must be excluded from being watched.
                               Has precedence on exclude_filter defined
                               into __init__.
        @type exclude_filter: bool
        @return: dict of paths associated to watch descriptors. A wd value
                 is positive if the watch has been sucessfully added,
                 otherwise the value is negative. If the path is invalid
                 it will be not included into this dict.
        @rtype: dict of {str: int}
        """
        ret_ = {} # return {path: wd, ...}

        if exclude_filter is None:
            exclude_filter = self._exclude_filter

        # normalize args as list elements
        for npath in self.__format_param(path):
            # unix pathname pattern expansion
            for apath in self.__glob(npath, do_glob):
                # recursively list subdirs according to rec param
                for rpath in self.__walk_rec(apath, rec):
                    if not exclude_filter(rpath):
                        wd = ret_[rpath] = self.__add_watch(rpath, mask,
                                                            proc_fun,
                                                            auto_add)
                        if wd < 0:
                            err = 'add_watch: cannot watch %s (WD=%d)'
                            err = err % (rpath, wd)
                            if quiet:
                                log.error(err)
                            else:
                                raise WatchManagerError(err, ret_)
                    else:
                        # Let's say -2 means 'explicitely excluded
                        # from watching'.
                        ret_[rpath] = -2
        return ret_

    def __get_sub_rec(self, lpath):
        """
        Get every wd from self._wmd if its path is under the path of
        one (at least) of those in lpath. Doesn't follow symlinks.

        @param lpath: list of watch descriptor
        @type lpath: list of int
        @return: list of watch descriptor
        @rtype: list of int
        """
        for d in lpath:
            root = self.get_path(d)
            if root:
                # always keep root
                yield d
            else:
                # if invalid
                continue

            # nothing else to expect
            if not os.path.isdir(root):
                continue

            # normalization
            root = os.path.normpath(root)
            # recursion
            lend = len(root)
            for iwd in self._wmd.items():
                cur = iwd[1].path
                pref = os.path.commonprefix([root, cur])
                if root == os.sep or (len(pref) == lend and \
                                      len(cur) > lend and \
                                      cur[lend] == os.sep):
                    yield iwd[1].wd

    def update_watch(self, wd, mask=None, proc_fun=None, rec=False,
                     auto_add=False, quiet=True):
        """
        Update existing watch(s). Both the mask and the processing
        object can be modified.

        @param wd: Watch Descriptor to update. Also accepts a list of
                     watch descriptors.
        @type wd: int or list of int
        @param mask: Optional new bitmask of events.
        @type mask: int
        @param proc_fun: Optional new processing function.
        @type proc_fun: function or ProcessEvent instance or instance of
                        one of its subclasses or callable object.
        @param rec: Recursively update watches on every already watched
                    subdirectories and subfiles.
        @type rec: bool
        @param auto_add: Automatically add watches on newly created
                         directories in the watch's path.
        @type auto_add: bool
        @param quiet: if False raises a WatchManagerError exception on
                      error. See example not_quiet.py
        @type quiet: bool
        @return: dict of watch descriptors associated to booleans values.
                 True if the corresponding wd has been successfully
                 updated, False otherwise.
        @rtype: dict of int: bool
        """
        lwd = self.__format_param(wd)
        if rec:
            lwd = self.__get_sub_rec(lwd)

        ret_ = {}  # return {wd: bool, ...}
        for awd in lwd:
            apath = self.get_path(awd)
            if not apath or awd < 0:
                err = 'update_watch: invalid WD=%d' % awd
                if quiet:
                    log.error(err)
                    continue
                raise WatchManagerError(err, ret_)

            if mask:
                addw = LIBC.inotify_add_watch
                wd_ = addw(self._fd, ctypes.create_string_buffer(apath), mask)
                if wd_ < 0:
                    ret_[awd] = False
                    err = 'update_watch: cannot update WD=%d (%s)' % (wd_,
                                                                      apath)
                    if quiet:
                        log.error(err)
                        continue
                    raise WatchManagerError(err, ret_)

                assert(awd == wd_)

            if proc_fun or auto_add:
                watch_ = self._wmd[awd]

            if proc_fun:
                watch_.proc_fun = proc_fun

            if auto_add:
                watch_.proc_fun = auto_add

            ret_[awd] = True
            log.debug('Updated watch - %s', self._wmd[awd])
        return ret_

    def __format_param(self, param):
        """
        @param param: Parameter.
        @type param: string or int
        @return: wrap param.
        @rtype: list of type(param)
        """
        if isinstance(param, list):
            for p_ in param:
                yield p_
        else:
            yield param

    def get_wd(self, path):
        """
        Returns the watch descriptor associated to path. This method
        has an prohibitive cost, always prefer to keep the WD.
        If path is unknown None is returned.

        @param path: path.
        @type path: str
        @return: WD or None.
        @rtype: int or None
        """
        path = os.path.normpath(path)
        for iwd in self._wmd.iteritems():
            if iwd[1].path == path:
                return iwd[0]
        log.debug('get_wd: unknown path %s', path)

    def get_path(self, wd):
        """
        Returns the path associated to WD, if WD is unknown
        None is returned.

        @param wd: watch descriptor.
        @type wd: int
        @return: path or None.
        @rtype: string or None
        """
        watch_ = self._wmd.get(wd)
        if watch_:
            return watch_.path
        log.debug('get_path: unknown WD %d', wd)

    def __walk_rec(self, top, rec):
        """
        Yields each subdirectories of top, doesn't follow symlinks.
        If rec is false, only yield top.

        @param top: root directory.
        @type top: string
        @param rec: recursive flag.
        @type rec: bool
        @return: path of one subdirectory.
        @rtype: string
        """
        if not rec or os.path.islink(top) or not os.path.isdir(top):
            yield top
        else:
            for root, dirs, files in os.walk(top):
                yield root

    def rm_watch(self, wd, rec=False, quiet=True):
        """
        Removes watch(s).

        @param wd: Watch Descriptor of the file or directory to unwatch.
                   Also accepts a list of WDs.
        @type wd: int or list of int.
        @param rec: Recursively removes watches on every already watched
                    subdirectories and subfiles.
        @type rec: bool
        @param quiet: if False raises a WatchManagerError exception on
                      error. See example not_quiet.py
        @type quiet: bool
        @return: dict of watch descriptors associated to booleans values.
                 True if the corresponding wd has been successfully
                 removed, False otherwise.
        @rtype: dict of int: bool
        """
        lwd = self.__format_param(wd)
        if rec:
            lwd = self.__get_sub_rec(lwd)

        ret_ = {}  # return {wd: bool, ...}
        for awd in lwd:
            # remove watch
            wd_ = LIBC.inotify_rm_watch(self._fd, awd)
            if wd_ < 0:
                ret_[awd] = False
                err = 'rm_watch: cannot remove WD=%d' % awd
                if quiet:
                    log.error(err)
                    continue
                raise WatchManagerError(err, ret_)

            ret_[awd] = True
            log.debug('watch WD=%d (%s) removed', awd, self.get_path(awd))
        return ret_


    def watch_transient_file(self, filename, mask, proc_class):
        """
        Watch a transient file, which will be created and deleted frequently
        over time (e.g. pid file).

        @attention: Under the call to this function it will be impossible
        to correctly watch the events triggered into the same
        base directory than the directory where is located this watched
        transient file. For instance it would actually be wrong to make these
        two successive calls: wm.watch_transient_file('/var/run/foo.pid', ...)
        and wm.add_watch('/var/run/', ...)

        @param filename: Filename.
        @type filename: string
        @param mask: Bitmask of events, should contain IN_CREATE and IN_DELETE.
        @type mask: int
        @param proc_class: ProcessEvent (or of one of its subclass), beware of
                           accepting a ProcessEvent's instance as argument into
                           __init__, see transient_file.py example for more
                           details.
        @type proc_class: ProcessEvent's instance or of one of its subclasses.
        @return: See add_watch().
        @rtype: See add_watch().
        """
        dirname = os.path.dirname(filename)
        if dirname == '':
            return {}  # Maintains coherence with add_watch()
        basename = os.path.basename(filename)
        # Assuming we are watching at least for IN_CREATE and IN_DELETE
        mask |= IN_CREATE | IN_DELETE

        def cmp_name(event):
            return basename == event.name
        return self.add_watch(dirname, mask,
                              proc_fun=proc_class(ChainIfTrue(func=cmp_name)),
                              rec=False,
                              auto_add=False, do_glob=False)


class Color:
    normal = "\033[0m"
    black = "\033[30m"
    red = "\033[31m"
    green = "\033[32m"
    yellow = "\033[33m"
    blue = "\033[34m"
    purple = "\033[35m"
    cyan = "\033[36m"
    bold = "\033[1m"
    uline = "\033[4m"
    blink = "\033[5m"
    invert = "\033[7m"

    @staticmethod
    def Punctuation(s):
        return Color.normal + s + Color.normal

    @staticmethod
    def FieldValue(s):
        if not isinstance(s, basestring):
            s = str(s)
        return Color.purple + s + Color.normal

    @staticmethod
    def FieldName(s):
        return Color.blue + s + Color.normal

    @staticmethod
    def ClassName(s):
        return Color.red + Color.bold + s + Color.normal

    @staticmethod
    def Simple(s, color):
        if not isinstance(s, basestring):
            s = str(s)
        try:
            color_attr = getattr(Color, color)
        except AttributeError:
            return s
        return color_attr + s + Color.normal


def command_line():
    #
    # - By default the watched path is '/tmp' for all events.
    # - The monitoring execution blocks and serve forever, type c^c
    #   to stop it.
    #
    from optparse import OptionParser

    usage = "usage: %prog [options] [path1] [path2] [pathn]"

    parser = OptionParser(usage=usage)
    parser.add_option("-v", "--verbose", action="store_true",
                      dest="verbose", help="Verbose mode")
    parser.add_option("-r", "--recursive", action="store_true",
                      dest="recursive",
                      help="Add watches recursively on paths")
    parser.add_option("-a", "--auto_add", action="store_true",
                      dest="auto_add",
                      help="Automatically add watches on new directories")
    parser.add_option("-e", "--events-list", metavar="EVENT[,...]",
                      dest="events_list",
                      help=("A comma-separated list of events to watch for - "
                           "see the documentation for valid options (defaults"
                           " to everything)"))
    parser.add_option("-s", "--stats", action="store_true",
                      dest="stats",
                      help="Display statistics")

    (options, args) = parser.parse_args()

    if options.verbose:
        log.setLevel(10)

    if len(args) < 1:
        path = '/tmp'  # default watched path
    else:
        path = args

    # watch manager instance
    wm = WatchManager()
    # notifier instance and init
    if options.stats:
        notifier = Notifier(wm, default_proc_fun=Stats(), read_freq=5)
    else:
        notifier = Notifier(wm)

    # What mask to apply
    mask = 0
    if options.events_list:
        events_list = options.events_list.split(',')
        for ev in events_list:
            evcode = EventsCodes.ALL_FLAGS.get(ev, 0)
            if evcode:
                mask |= evcode
            else:
                parser.error("The event '%s' specified with option -e"
                             " is not valid" % ev)
    else:
        mask = ALL_EVENTS

    # stats
    cb_fun = None
    if options.stats:
        def cb(s):
            print('%s\n%s\n' % (repr(s.proc_fun()),
                                s.proc_fun()))
        cb_fun = cb

    log.debug('Start monitoring %s, (press c^c to halt pyinotify)' % path)

    wm.add_watch(path, mask, rec=options.recursive, auto_add=options.auto_add)
    # Loop forever (until sigint signal get caught)
    notifier.loop(callback=cb_fun)


if __name__ == '__main__':
    command_line()

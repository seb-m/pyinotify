#!/usr/bin/env python

# check Python's version
import sys
if sys.version < '2.4':
    sys.stderr.write('This module requires Python 2.4 or later.\n')
    sys.exit(1)

# import statements
from distutils.core import setup, Extension
from distutils.util import get_platform

# debug
DISTUTILS_DEBUG = True

# get platform
platform = get_platform()

# check linux platform
if not platform.startswith('linux'):
    raise Exception, "inotify not available under %s" % platform

classif=[
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Natural Language :: English',
    'Operating System :: POSIX :: Linux',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries',
    'Topic :: System :: Monitoring'
    ]

setup(
    name='pyinotify',
    version='0.8.0',
    description='Filesystem monitoring, use inotify',
    author='Sebastien Martini',
    author_email='sebastien.martini@gmail.com',
    license='GPL 2',
    platforms='Linux',
    classifiers=classif,
    url='http://seb.dbzteam.org/pages/pyinotify-dev.html',
    download_url='http://git.dbzteam.org/?p=pyinotify.git;a=snapshot;h=HEAD;sf=tgz',
    py_modules=['pyinotify'],
    )

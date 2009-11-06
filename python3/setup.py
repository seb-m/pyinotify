#!/usr/bin/env python

# check Python's version
import sys
if sys.version < '3.0':
    sys.stderr.write('This module requires Python 3.0 or later.\n')
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
    raise Exception, "inotify is not available under %s" % platform

classif=[
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Natural Language :: English',
    'Operating System :: POSIX :: Linux',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Topic :: Software Development :: Libraries',
    'Topic :: System :: Monitoring',
    ]

setup(
    name='pyinotify',
    version='0.8.8',
    description='Linux filesystem events monitoring',
    author='Sebastien Martini',
    author_email='sebastien.martini@gmail.com',
    license='GPLv2+',
    platforms='Linux',
    classifiers=classif,
    url='http://trac.dbzteam.org/pyinotify',
    download_url='http://seb.dbzteam.org/pub/pyinotify/releases/pyinotify-0.8.8.tar.gz',
    py_modules=['pyinotify'],
    )

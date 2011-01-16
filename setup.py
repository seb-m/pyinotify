#!/usr/bin/env python

# check Python's version
import sys
if sys.version < '2.4':
    sys.stderr.write('This module requires at least Python 2.4\n')
    sys.exit(1)

# import statements
from distutils.core import setup, Extension
from distutils.util import get_platform

# debug
DISTUTILS_DEBUG = False

# get platform
platform = get_platform()

# check linux platform
if not platform.startswith('linux'):
    sys.stderr.write("inotify is not available under %s\n" % platform)
    sys.exit(1)

classif = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Operating System :: POSIX :: Linux',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.4',
    'Programming Language :: Python :: 2.5',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.0',
    'Programming Language :: Python :: 3.1',
    'Programming Language :: Python :: 3.2',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: System :: Filesystems',
    'Topic :: System :: Monitoring',
    ]

if sys.version_info[0] >= 3:
    package_dir = {'': 'python3'}
else:
    package_dir = {'': 'python2'}

setup(
    name='pyinotify',
    version='0.9.1',
    description='Linux filesystem events monitoring',
    author='Sebastien Martini',
    author_email='seb@dbzteam.org',
    license='MIT License',
    platforms='Linux',
    classifiers=classif,
    url='http://github.com/seb-m/pyinotify',
    download_url='http://seb.dbzteam.org/pub/pyinotify/releases/pyinotify-0.9.1.tar.gz',
    py_modules=['pyinotify'],
    package_dir=package_dir,
    packages=[''],
    )

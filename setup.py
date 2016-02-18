#!/usr/bin/env python

# Set True to force compile native C-coded extension providing direct access
# to inotify's syscalls. If set to False this extension will only be compiled
# if no inotify interface from ctypes is found.
compile_ext_mod = False

# import statements
import os
import sys
import distutils.extension
from distutils.util import get_platform
from setuptools.command.install import install


try:
    # First try to load most advanced setuptools setup.
    from setuptools import setup
except:
    # Fall back if setuptools is not installed.
    from distutils.core import setup


platform = get_platform()


class InstallCommand(install):
    user_options = install.user_options + [
        ('no-platform-check', None, 'Default?')
    ]

    def initialize_options(self):
        install.initialize_options(self)
        self.no_platform_check = None

    def run(self):
        global platform
        if not platform.startswith('linux') and \
                not platform.startswith('freebsd'):
            if self.no_platform_check is not None:
                sys.stdout.write(
                    "inotify is not available on %s,"
                    "but check is ignored\n" % platform)
            else:
                # check linux platform
                sys.stderr.write(
                        "inotify is not available on %s "
                        "(--no-platform-check forces install)\n" % platform)
                sys.exit(1)
        install.run(self)


# check Python's version
if sys.version_info < (2, 4):
    sys.stderr.write('This module requires at least Python 2.4\n')
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
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: Implementation :: CPython',
    'Programming Language :: Python :: Implementation :: PyPy',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: System :: Filesystems',
    'Topic :: System :: Monitoring',
    ]


# Select branch
if sys.version_info >= (3, 0):
    package_dir = {'': 'python3'}
else:
    package_dir = {'': 'python2'}


def should_compile_ext_mod():
    try:
        import ctypes
        import ctypes.util
    except:
        return True

    try_libc_name = 'c'
    if platform.startswith('freebsd'):
        try_libc_name = 'inotify'

    libc_name = None
    try:
        libc_name = ctypes.util.find_library(try_libc_name)
    except:
        pass  # Will attemp to load it with None anyway.

    libc = ctypes.CDLL(libc_name)
    # Eventually check that libc has needed inotify bindings.
    if (not hasattr(libc, 'inotify_init') or
            not hasattr(libc, 'inotify_add_watch') or
            not hasattr(libc, 'inotify_rm_watch')):
        return True
    return False


if compile_ext_mod or should_compile_ext_mod():
    # add -fpic if x86_64 arch
    if platform in ["linux-x86_64"]:
        os.environ["CFLAGS"] = "-fpic"
    # sources for ext module
    # dst for ext module
    ext_mod_src = ['common/inotify_syscalls.c']

ext_mod = [distutils.extension.Extension('inotify_syscalls', ext_mod_src)]

setup(
    cmdclass={
        'install': InstallCommand
    },
    name='pyinotify',
    version='0.9.6',
    description='Linux filesystem events monitoring',
    author='Sebastien Martini',
    author_email='seb@dbzteam.org',
    license='MIT License',
    platforms='Linux',
    classifiers=classif,
    url='http://github.com/seb-m/pyinotify',
    download_url='http://pypi.python.org/pypi/pyinotify',
    ext_modules=ext_mod,
    py_modules=['pyinotify'],
    package_dir=package_dir,
    )

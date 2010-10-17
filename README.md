# Pyinotify

* License           : MIT
* Project URL       : [http://github.com/seb-m/pyinotify](http://github.com/seb-m/pyinotify)
* Project Wiki      : [http://github.com/seb-m/pyinotify/wiki](http://github.com/seb-m/pyinotify/wiki)
* API Documentation : [http://seb-m.github.com/pyinotify](http://seb-m.github.com/pyinotify)
* Examples          : [http://github.com/seb-m/pyinotify/tree/master/python2/examples/](http://github.com/seb-m/pyinotify/tree/master/python2/examples/)


## Dependencies

* Linux >= 2.6.13
* Python (CPython) >= 2.4
* Libc with inotify support (usually version >= 2.4 for GLibc)
* ctypes (part of the standard library since Python 2.5)
* Epydoc (optional, used to generate html documentation from docstrings)


## Install

### Install from the distributed tarball

    # Choose your Python interpreter: either python, python2.6, python3.1,..
    # Replacing XXX accordingly with your previous choice type:
    $ sudo pythonXXX setup.py install

### Or install it with "Easy Install" (currently seems to work only for Python2)

    $ wget http://peak.telecommunity.com/dist/ez_setup.py
    $ sudo python ez_setup.py
    $ sudo easy_install pyinotify


## Watch a directory

Install pyinotify and run this command from a shell:

    $ python -m pyinotify -v /my-dir-to-watch

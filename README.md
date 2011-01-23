# Pyinotify

* License           : MIT
* Project URL       : [http://github.com/seb-m/pyinotify](http://github.com/seb-m/pyinotify)
* Project Wiki      : [http://github.com/seb-m/pyinotify/wiki](http://github.com/seb-m/pyinotify/wiki)
* API Documentation : [http://seb-m.github.com/pyinotify](http://seb-m.github.com/pyinotify)


## Dependencies

* Linux ≥ 2.6.13
* Python ≥ 2.4
* A libc with inotify's binding
* ctypes


## Install

### Install from the distributed tarball

    # Choose your Python interpreter: either python, python2.6, python3.1,..
    # Replacing XXX accordingly, type:
    $ sudo pythonXXX setup.py install

### Or install it with `easy_install` (currently seems to be available only for Python2)

    # Install easy_install
      $ sudo apt-get install setuptools
    # Or alternatively, this way
      $ wget http://peak.telecommunity.com/dist/ez_setup.py
      $ sudo python ez_setup.py
    # Finally, install Pyinotify
    $ sudo easy_install pyinotify


## Watch a directory

Install pyinotify and run this command from a shell:

    $ python -m pyinotify -v /my-dir-to-watch

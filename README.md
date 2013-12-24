# Pyinotify

* License          : MIT
* Project URL      : [http://github.com/seb-m/pyinotify](http://github.com/seb-m/pyinotify)
* Project Wiki     : [http://github.com/seb-m/pyinotify/wiki](http://github.com/seb-m/pyinotify/wiki)
* API Documentation: [http://seb-m.github.com/pyinotify](http://seb-m.github.com/pyinotify)
* Test Status      : [![tests status](https://secure.travis-ci.org/seb-m/pyinotify.png?branch=master)](https://travis-ci.org/seb-m/pyinotify)
* Coverage Status  : [![Coverage Status](https://coveralls.io/repos/seb-m/pyinotify/badge.png?branch=master)](https://coveralls.io/r/seb-m/pyinotify)


## Dependencies

* Linux ≥ 2.6.13
* Python ≥ 2.4 (including Python 3.x)


## Install

### Get the current stable version from PyPI and install it with `pip`

    # To install pip follow http://www.pip-installer.org/en/latest/installing.html
    $ sudo pip install pyinotify

### Or install Pyinotify directly from source

    # Choose your Python interpreter: either python, python2.7, python3.2,..
    # Replacing XXX accordingly, type:
    $ sudo pythonXXX setup.py install


## Watch a directory

Install pyinotify and run this command from a shell:

    $ python -m pyinotify -v /my-dir-to-watch

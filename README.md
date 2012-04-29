# Pyinotify

* License          : MIT
* Project URL      : [http://github.com/seb-m/pyinotify](http://github.com/seb-m/pyinotify)
* Project Wiki     : [http://github.com/seb-m/pyinotify/wiki](http://github.com/seb-m/pyinotify/wiki)
* API Documentation: [http://seb-m.github.com/pyinotify](http://seb-m.github.com/pyinotify)


## Dependencies

* Linux ≥ 2.6.13
* Python ≥ 2.4


## Install

### Install Pyinotify using the distribution source

    # Choose your Python interpreter: either python, python2.6, python3.1,..
    # Replacing XXX accordingly, type:
    $ sudo pythonXXX setup.py install


### Or get the current package from PyPI and install it with `pip` or `easy_install`

    # To install pip follow http://www.pip-installer.org/en/latest/installing.html
    # easy_install is bundled with setuptools
    $ sudo easy_install pyinotify
    $ sudo pip install pyinotify


## Watch a directory

Install pyinotify and run this command from a shell:

    $ python -m pyinotify -v /my-dir-to-watch

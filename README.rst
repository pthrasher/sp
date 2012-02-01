==
sp
==

I used to work for Turner Broadcasting, and we used an internal perl script
named sp to find files hogging disk space on a server. I have long ago left
Turner, and never brought the source code along with me, so I decided to
re-write it in python.

In a nutshell, here's what it does:

  * Recurse through directories from a starting point (current working dir, or
    a directory you specify)
  * Gather all file sizes, and therefore, also directory sizes.
  * List all directories largest to smallest, and same for files.
  * Be able to ignore files less than a certain size while still letting their
    size count toward their parent directorie's size.
  * Be able to ignore directories less than a certain size while still letting
    their size count toward their parent directorie's size.
  * Limit number of files displayed per directory. For instance... Show only
    the top 15 largest files.
  * Limit depth to recurse.

Installation
------------

sp uses setuptools_ for installation. It has no dependencies. sp is
easy_installable::

  $ easy_install sp

Alternatively, download and unpack the tarball and install::

  $ tar zxf sp-1.0.0.tar.gz
  $ python setup.py install

On UNIX systems, use sudo for the latter command if you need to install the
scripts to a directory that requires root privileges::

  $ sudo python setup.py install

The development git repository can be checked out anonymously::

  $ git clone https://github.com/pthrasher/sp.git

There is one little tweak to the installation that you may want to consider. By
default, setuptools installs scripts indirectly; the scripts installed to
$prefix/bin or Python2x\Scripts use setuptools' pkg_resources module to load
the exact version of sp egg that installed the script, then runs the script's
main() function. This is not usually a bad feature, but it can add substantial
startup overhead for a small command-line utility like sp. If you want the
response of sp to be snappier, I recommend installing custom scripts that just
import the sp module and run the sp_main() function. See the file
examples/sp for an example.

.. _setuptools : http://pypi.python.org/pypi/setuptools


Using sp
----------

To recursively search from the current directory with default settings:

  $ sp

To do anything else, see the help.

  $ sp --help


To Do
-----

* Add file / folder exclusion list.


Bugs and Such
-------------

If you find a bug, or a missing feature you really want added, please post to
the issue-tracker_ on github.com or email the author at
<philipthrasher@gmail.com>.

.. _issue-tracker : https://github.com/pthrasher/sp/issues


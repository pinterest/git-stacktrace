git-stacktrace
==============

git-stacktrace is designed to make it easy to figure out which commit caused a given stacktrace.

git-stacktrace looks for:

* commits in given range that touched files in the stacktrace
* commits in given range that added/removed code present the stacktrace


Supported Languages
-------------------

* Python
* Java


Development
------------

Run tests with: ``tox``

Installation
------------

.. code-block:: sh

    $ pip install git_stacktrace

Usage
-----

For the CLI see: ``git stacktrace -h``

For the Python API see: ``git_stacktrace/api.py``


Examples
--------

Example output::


    $ git stacktrace --since=1.day < trace
    Traceback (most recent call last):
     File "webapp/framework/resource.py", line 72, in _call
       result = getattr(self, method_name)()
     File "webapp/resources/interests_resource.py", line 232, in get
       if self.options['from_navigate'] == "true":
    KeyError


    commit da39a3ee5e6b4b0d3255bfef95601890afd80709
    Commit Date: Tue, 19 Jul 2016 14:18:08 -0700
    Author:      John Doe <johndoe@pinterest.com>
    Subject:     break interest resource
    Link:        https://example.com/D1000
    Files Modified:
       - webapp/resources/interests_resource.py:232
    Lines Added:
       - "if self.options['from_navigate'] == "true":"

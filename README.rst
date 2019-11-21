git-stacktrace
==============

git-stacktrace is a tool to help you associate git commits with stacktraces.

It helps you identify related commits by looking at:

* commits in given range that touched files present in the stacktrace
* commits in given range that added/removed code present in the stacktrace

Supported Languages
-------------------

* Python
* Java
* `JavaScript <https://v8.dev/docs/stack-trace-api>`_

Development
------------

Run tests with: ``tox``

Installation
------------

.. code-block:: sh

    $ pip install git_stacktrace

Usage
-----

Run ``git stacktrace`` within a git initialized directory.

.. code-block:: sh

    usage: git stacktrace [<options>] [<RANGE>] < stacktrace from stdin

    Lookup commits related to a given stacktrace.

    positional arguments:
      range                 git commit range to use

    optional arguments:
      -h, --help            show this help message and exit
      --since <date1>       show commits more recent than a specific date (from
                            git-log)
      --server              start a webserver to visually interact with git-
                            stacktrace
      --port PORT           Server port
      -f, --fast            Speed things up by not running pickaxe if the file for
                            a line of code cannot be found
      -b [BRANCH], --branch [BRANCH]
                            Git branch. If using --since, use this to specify
                            which branch to run since on. Runs on current branch
                            by default
      --version             show program's version number and exit
      -d, --debug           Enable debug logging


For the Python API see: ``git_stacktrace/api.py``

To run as a web server: ``git stacktrace --server --port=8080``
or ``GIT_STACKTRACE_PORT=8080 git stacktrace --server``

Use the web server as an API:

.. code-block:: sh

    $ curl \
      -d '{"option-type":"by-date", "since":"1.day", "trace":"..."}' \
      -H "Content-Type: application/json" \
      -X POST http://localhost:8080/


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

git-stacktrace
==============

Use git to figure out what commits are related to a stacktrace


Development
------------

Run tests with: `tox`

Installation
-------------

TODO

`pip install git-stacktrace`

Usage
-----

see `git stacktrace -h`


Examples
----------

Example output:

    $ git stacktrace 04402ca..9f779bf traceback.txt
    Traceback:
     File "/mnt/builds/VXmUJO4bRX26CecfwlI_hw_9f779bf/webapp/denzel/resource.py", line 72, in _call
       result = getattr(self, method_name)()
     File "/mnt/builds/VXmUJO4bRX26CecfwlI_hw_9f779bf/webapp/resources/interests_resource.py", line 232, in get
       if self.options['from_navigate'] == "true":
    
    df342e4 Maintains unauth interest/topic signup modal experience.
    Differential Revision: https://phabricator.pinadmin.com/D92059
    files:
       - webapp/resources/interests_resource.py
    lines added:
       - "if self.options['from_navigate'] == "true":"

Sample stacktraces (from `git_stacktrace/tests/examples/`) and ranges:

* trace1: 95f8278..fdf4c43
* trace4: 81a25be..b3864b2
* trace5: 04402ca..9f779bf
* trace6: 04402ca..9f779bf

git-stacktrace
===============

Lookup commits related to a given stacktrace


Installation
-------------

TODO

`pip install git-stacktrace`

usage
-----

see `git stacktrace -h`


Example
---------

<pre><code>
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

</code></pre>

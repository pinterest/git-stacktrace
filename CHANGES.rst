Change Log
==========

0.7.2
-----

* Fix python traceback parsing with no code on last line (https://github.com/pinterest/git-stacktrace/pull/13)

0.7.1
-----

* Fix python traceback parsing where code is missing (https://github.com/pinterest/git-stacktrace/issues/10)
* Add --debug flag

0.7.0
-----

* Add python 3 support

0.6.0
-----

* Support arbitrary sized abbreviated hashes
* Clarify CLI help message

0.5.0
-----

* Match file line numbers in stacktrace to lines changed in commits
* Differentiate files added, deleted and modified
* print stacktrace headers and footers
* Fix git pickaxe error (Use '--' to separate paths from revisions)
* Add initial java stacktrace support. Begin supporting basic java stacktraces, some more complex formats are not supported yet.

0.4.1
-----

* Get ready for pypi

0.4.0
-----

* Initial open source commit

from __future__ import print_function

import collections
import re
import subprocess
import sys
import shlex
import os

import six
import whatthepatch

SHA1_REGEX = re.compile(r'\b[0-9a-f]{40}\b')


class GitFile(object):
    """Track filename and if file was added/removed or modified."""
    ADDED = 'A'
    DELETED = 'D'
    MODIFIED = 'M'
    COPY_EDIT = 'C'
    RENAME_EDIT = 'R'
    VALID = frozenset([ADDED, DELETED, MODIFIED, COPY_EDIT, RENAME_EDIT])

    def __init__(self, filename, state=None):
        self.filename = filename
        if state not in GitFile.VALID:
            raise Exception("Invalid git file state: %s" % state)
        self.state = state

    def __repr__(self):
        return self.filename

    def __eq__(self, other):
        if isinstance(other, six.string_types):
            other_filename = other
        else:
            other_filename = other.filename
        return self.filename == other_filename


def run_command_status(*argv, **kwargs):
    if len(argv) == 1:
        # for python2 compatibility with shlex
        if sys.version_info < (3,) and isinstance(argv[0], unicode):
            argv = shlex.split(argv[0].encode('utf-8'))
        else:
            argv = shlex.split(str(argv[0]))
    stdin = kwargs.pop('stdin', None)
    newenv = os.environ.copy()
    newenv['LANG'] = 'C'
    newenv['LANGUAGE'] = 'C'
    newenv.update(kwargs)
    p = subprocess.Popen(argv,
                         stdin=subprocess.PIPE if stdin else None,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         env=newenv)
    (out, nothing) = p.communicate(stdin)
    out = out.decode('utf-8', 'replace')
    return (p.returncode, out.strip())


def run_command(*argv, **kwargs):
    (rc, output) = run_command_status(*argv, **kwargs)
    if rc != 0:
        print(argv, rc, output)
        raise Exception("Something went wrong running the command %s %s" % (argv, kwargs))
    return output


def files_touched(git_range):
    """Run git log --pretty="%H" --raw  git_range.

    Generate a dictionary of files modified by the commits in range
    """
    cmd = 'git', 'log', '--pretty=%H', '--raw', git_range
    data = run_command(*cmd)
    commits = collections.defaultdict(list)
    commit = None
    for line in data.splitlines():
        if SHA1_REGEX.match(line):
            commit = line
        elif line.strip():
            split_line = line.split('\t')
            filename = split_line[-1]
            state = split_line[0].split(' ')[-1][0]
            commits[commit].append(GitFile(filename, state))
    return commits


def pickaxe(snippet, git_range, filename=None):
    """Run git log -S <snippet> <git_range> <filename>

    Use git pickaxe to 'Look for differences that change the number of occurrences of the
    specified string'

    If filename is passed in only look in that file

    Return list of commits that modified that snippet
    """
    cmd = 'git', 'log', '-b', '--pretty=%H', '-S', snippet.decode('string_escape'), git_range
    if filename:
        cmd = cmd + ('--', filename,)
    commits = run_command(*cmd).splitlines()
    commits = [(commit, line_removed(snippet, commit)) for commit in commits]
    # Couldn't find a good way to POSIX regex escape the code and use regex
    # pickaxe to match full lines, so filter out partial results here.
    # Filter out results that aren't a full line
    commits = [commit for commit in commits if commit[1] is not None]
    return commits


def line_removed(target_line, commit):
    """Given a commit tell if target_line was added or removed.

    True if line was removed
    False if added
    None if target_line wasn't found at all (because not a full line etc.)
    """
    cmd = 'git', 'log', '-1', '--format=', '-p', str(commit)
    diff = run_command(*cmd)
    for diff in whatthepatch.parse_patch(diff):
        for line in diff.changes:
            if target_line in line[2]:
                if line[0] is None:
                    # Line added
                    return False
                elif line[1] is None:
                    # Line removed
                    return True
    # target_line matched part of a line instead of a full line
    return None


def line_match(commit, traceback_line):
    """Return true if line_number was added to filename in commit"""

    cmd = 'git', 'log', '-1', '--format=', '-p', str(commit)
    diff = run_command(*cmd)
    for diff in whatthepatch.parse_patch(diff):
        if diff.header.new_path == traceback_line.git_filename:
            for line in diff.changes:
                if line[0] is None:
                    if line[1] == traceback_line.line_number:
                        return True
    return False


def format_one_commit(commit):
    result = []
    custom, full, url = get_commit_info(commit)
    result.append(custom)
    if url:
        result.append("Link:        " + url)
    return '\n'.join(result)


def get_commit_info(commit, color=True):
    # Only use color if output is a terminal
    if sys.stdout.isatty() and color:
        cmd_prefix = 'git', 'log', '--color', '-1'
    else:
        cmd_prefix = 'git', 'log', '-1'
    git_format = ('--format=%C(auto,yellow)commit %H%C(auto,reset)%n'
                  'Commit Date: %cD%nAuthor:      %aN <%aE>%nSubject:     %s')
    custom = run_command(*(cmd_prefix + (git_format, commit)))

    # Find phabricator URL
    cmd = 'git', 'log', '-1', '--pretty=%b', commit
    full = run_command(*cmd)
    url = None
    for line in full.splitlines():
        if line.startswith("Differential Revision:"):
            url = line.split(' ')[2]
    return custom, full, url


def valid_range(git_range):
    """Make sure there are commits in the range

    Generate a dictionary of files modified by the commits in range
    """
    cmd = 'git', 'log', '--oneline', git_range
    data = run_command(*cmd)
    lines = data.splitlines()
    return len(lines) > 0


def convert_since(since, branch=None):
    cmd = 'git', 'log', '--pretty=%H', "--since=%s" % since
    if branch:
        cmd = cmd + (branch,)
    data = run_command(*cmd)
    lines = data.splitlines()
    if len(lines) == 0:
        raise Exception("Didn't find any commits in 'since' range, try updating your git repo")
    return "%s..%s" % (lines[-1], lines[0])


def files(git_range):
    commit = git_range.split('.')[-1]
    cmd = 'git', 'ls-tree', '-r', '--name-only', commit
    data = run_command(*cmd)
    files = data.splitlines()
    return files

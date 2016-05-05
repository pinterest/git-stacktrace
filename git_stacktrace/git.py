import collections
import re
import subprocess
import sys
import shlex
import os


SHA1_REGEX = re.compile(r'\b[0-9a-f]{40}\b')


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
        print rc, output
        raise Exception("Something went wrong running the command %s %s" % (argv, kwargs))
    return output


def files_touched(git_range):
    """Run git log --pretty="%H" --numstat git_range.

    Generate a dictionary of files modified by the commits in range
    """
    cmd = 'git', 'log', '--pretty=%H', '--name-only', git_range
    data = run_command(*cmd)
    commits = collections.defaultdict(list)
    commit = None
    for line in data.splitlines():
        if SHA1_REGEX.match(line):
            commit = line
        elif line.strip():
            commits[commit].append(line)
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
        cmd = cmd + (filename,)
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
    lines = run_command(*cmd).splitlines()
    for line in lines:
        check = False
        removed = False
        if line.startswith('-'):
            removed = True
            check = True
        elif line.startswith('+'):
            check = True
        if check and target_line == line[1:].strip():
            return removed
    # target_line matched part of a line instead of a full line
    return None


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


def convert_since(since, path=None):
    cmd = 'git', 'log', '--pretty=%H', "--since=%s" % since
    if path:
        cmd = cmd + (path,)
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

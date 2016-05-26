import subprocess
import sys
import shlex
import os


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
    cmd = 'git', 'log', '--pretty=%H', '--numstat', git_range
    data = run_command(*cmd)
    commits = {}
    commit = None
    lines = []
    for line in data.splitlines():
        tokens = line.split('\t')
        if len(tokens) == 1:
            # Must be a hash
            if len(tokens[0]) == 0:
                # empty line
                continue
            if commit is not None:
                # Found next commit
                commits[commit] = lines
                lines = []
                commit = None
            commit = tokens[0]
        elif len(tokens) == 0:
            # blank line
            pass
        elif len(tokens) == 3:
            # file diff and names
            lines.append(tokens[2])
        else:
            raise Exception("Something went wrong parsing git log")
    return commits


def pickaxe(snippet, git_range):
    """Run git log -S <snippet> <git_range>.

    Use git pickaxe to 'Look for differences that change the number of occurrences of the
    specified string'

    Return list of commits that modified that snippet
    """
    cmd = 'git', 'log', '--pretty=%H', '-S', snippet.decode('string_escape'), git_range
    commits = run_command(*cmd).splitlines()
    return commits


def print_one_commit(commit, oneline=False):
    if oneline:
        cmd = 'git', 'log', '--color', '-1', '--oneline', commit
        print run_command(*cmd)
    else:
        cmd = 'git', 'log', '-1', '--pretty=short', commit
        print run_command(*cmd)
        # Find phabricator URL
        cmd = 'git', 'log', '-1', '--pretty=%b', commit
        body = run_command(*cmd)
        for line in body.splitlines():
            if line.startswith("Differential Revision:"):
                print line


def valid_range(git_range):
    """Make sure there are commits in the range

    Generate a dictionary of files modified by the commits in range
    """
    cmd = 'git', 'log', '--oneline', git_range
    data = run_command(*cmd)
    lines = data.splitlines()
    return len(lines) > 0

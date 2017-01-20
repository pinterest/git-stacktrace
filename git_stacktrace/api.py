"""
python API to call git stacktrace.


Example usage:
    from git_stacktrace import api

    traceback = api.parse_trace(traceback_string)
    git_range = api.convert_since('1.day')
    results = api.lookup_stacktrace(traceback, git_range, fast=False)
    for r in results.get_sorted_results():
        print ""
        print r
"""


from git_stacktrace import git
from git_stacktrace import result
from git_stacktrace import parse_trace

# So we can call api.parse_trace
parse_trace = parse_trace.parse_trace


def _longest_filename(matches):
    """find longest match by number of '/'."""
    return max(matches, key=lambda filename: len(filename.split('/')))


def _lookup_files(commit_files, git_files, traceback, results):
    """Populate results and line.git_filename."""
    for line in traceback.lines:
        matches = traceback.file_match(line.trace_filename, git_files)
        if matches:
            git_file = _longest_filename(matches)
            for commit, file_list in commit_files.items():
                if git_file in file_list:
                    git_file = file_list[file_list.index(git_file)]
                    line.git_filename = git_file.filename
                    line_number = None
                    if git.line_match(commit, line):
                        line_number = line.line_number
                    results.get_result(commit).add_file(git_file, line_number)
            if line.git_filename is None:
                line.git_filename = _longest_filename(matches)


def convert_since(since, branch=None):
    """Convert the git since format into a git range

    since -- git formatted since value such as '1,day'
    branch -- git branch, such as 'origin/master'
    """
    return git.convert_since(since, branch=branch)


def valid_range(git_range):
    """Make sure there are commits in the range

    Generate a dictionary of files modified by the commits in range
    """
    return git.valid_range(git_range)


def lookup_stacktrace(traceback, git_range, fast):
    """Lookup to see what commits in git_range could have caused the stacktrace.

    If fast is True, don't run pickaxe if cannot find the file in git.

    Pass in a stacktrace object and returns a results object."""
    results = result.Results()

    commit_files = git.files_touched(git_range)
    git_files = git.files(git_range)
    _lookup_files(commit_files, git_files, traceback, results)

    for line in traceback.lines:
        commits = []
        if not (line.git_filename is None and fast is True):
            try:
                commits = git.pickaxe(line.code, git_range, line.git_filename)
            except Exception:
                # If this fails, move on
                continue
        for commit, line_removed in commits:
            if line_removed is True:
                results.get_result(commit).lines_removed.add(line.code)
            if line_removed is False:
                results.get_result(commit).lines_added.add(line.code)
    return results

from git_stacktrace import git
from git_stacktrace import result


def _lookup_files(commit_files, git_files, traceback, results):
    """Populate results and line.git_filename."""
    for line in traceback.lines:
        matches = [f for f in git_files if line.trace_filename.endswith(f)]
        if matches:
            git_file = max([f for f in git_files if line.trace_filename.endswith(f)], key=lambda x: len(x))
            for commit, file_list in commit_files.iteritems():
                if git_file in file_list:
                    line.git_filename = git_file
                    results.get_result(commit).files.add(git_file)


def lookup_stacktrace(traceback, git_range):
    """Lookup to see what commits in git_range could have caused the stacktrace.

    Pass in a stacktrace object and returns a results object."""
    results = result.Results()

    commit_files = git.files_touched(git_range)
    git_files = git.files(git_range)
    _lookup_files(commit_files, git_files, traceback, results)

    for line in traceback.lines:
        try:
            commits = git.pickaxe(line.code, git_range, line.git_filename)
        except Exception:
            continue
        for commit, line_removed in commits:
            if line_removed:
                results.get_result(commit).lines_removed.add(line.code)
            else:
                results.get_result(commit).lines_added.add(line.code)
    return results

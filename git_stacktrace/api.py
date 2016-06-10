from git_stacktrace import git
from git_stacktrace import result


def _lookup_files(commit_files, traceback, results):
    """Populate results and line.git_filename."""
    for commit, file_list in commit_files.iteritems():
        for git_file in file_list:
            for line in traceback.lines:
                if git_file in line.trace_filename:
                    line.git_filename = git_file
                    results.get_result(commit).files.add(git_file)


def lookup_stacktrace(traceback, git_range):
    # TODO docs and tests
    results = result.Results()

    commit_files = git.files_touched(git_range)
    _lookup_files(commit_files, traceback, results)

    for line in traceback.lines:
        commits = git.pickaxe(line.code, git_range, line.git_filename)
        for commit, line_removed in commits:
            if line_removed:
                results.get_result(commit).lines_removed.add(line.code)
            else:
                results.get_result(commit).lines_added.add(line.code)
    return results

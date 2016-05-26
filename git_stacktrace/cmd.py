import argparse

from git_stacktrace import parse_trace
from git_stacktrace import git
from git_stacktrace import result


def lookup_files(commit_files, traceback, results):
    """Populate results and line.git_filename."""
    for commit, file_list in commit_files.iteritems():
        for git_file in file_list:
            for line in traceback.lines:
                if git_file in line.trace_filename:
                    line.git_filename = git_file
                    results.get_result(commit).files.add(git_file)


def main():
    usage = "git stacktrace [RANGE] [STACKTRACE IN FILE]"
    description = "Lookup commits related to a given stacktrace"
    parser = argparse.ArgumentParser(usage=usage, description=description)
    parser.add_argument('range', help='git commit range to use')
    parser.add_argument('stacktrace', help='stacktrace filename')
    args = parser.parse_args()

    if not git.valid_range(args.range):
        print "Found no commits in '%s'" % args.range
        exit(1)

    traceback = parse_trace.Traceback(filename=args.stacktrace)

    traceback.print_traceback()

    results = result.Results()

    commit_files = git.files_touched(args.range)
    lookup_files(commit_files, traceback, results)

    for line in traceback.lines:
        commits = git.pickaxe(line.code, args.range, line.git_filename)
        for commit in commits:
            results.get_result(commit).snippets.add(line.code)

    for r in results.get_sorted_results():
        print ""
        git.print_one_commit(r.commit, oneline=True)
        print r

if __name__ == "__main__":
    main()

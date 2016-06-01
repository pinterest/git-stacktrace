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
    usage = "git stacktrace [<options>] [<RANGE>] <STACKTRACE IN FILE>"
    description = "Lookup commits related to a given stacktrace"
    parser = argparse.ArgumentParser(usage=usage, description=description)
    range_group = parser.add_mutually_exclusive_group()
    range_group.add_argument('--since', metavar="<date1>", help='show commits '
                             'more recent then a specific date (from git-log)')
    range_group.add_argument('range', nargs='?', help='git commit range to use')
    parser.add_argument('stacktrace', help='stacktrace filename')
    args = parser.parse_args()

    if args.since:
        git_range = git.convert_since(args.since)
    else:
        git_range = args.range

    if not git.valid_range(git_range):
        print "Found no commits in '%s'" % git_range
        exit(1)

    traceback = parse_trace.Traceback(filename=args.stacktrace)

    traceback.print_traceback()

    results = result.Results()

    commit_files = git.files_touched(git_range)
    lookup_files(commit_files, traceback, results)

    for line in traceback.lines:
        commits = git.pickaxe(line.code, git_range, line.git_filename)
        for commit, line_removed in commits:
            if line_removed:
                results.get_result(commit).lines_removed.add(line.code)
            else:
                results.get_result(commit).lines_added.add(line.code)

    for r in results.get_sorted_results():
        print ""
        git.print_one_commit(r.commit, oneline=True)
        print r

    if len(results.get_sorted_results()) == 0:
        print "No matches found"

if __name__ == "__main__":
    main()

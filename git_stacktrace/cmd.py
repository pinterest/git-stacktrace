import argparse
import collections

from git_stacktrace import parse_trace
from git_stacktrace import git


def lookup_file(commit_files, trace_files):
    commits = collections.defaultdict(list)
    for commit, file_list in commit_files.iteritems():
        for git_file in file_list:
            for f in trace_files:
                if git_file in f:
                    commits[commit].append(git_file)
    return commits


def main():
    usage = "git stacktrace [RANGE] [STACKTRACE FILE]"
    description = "Lookup commits related to a given stacktrace"
    parser = argparse.ArgumentParser(usage=usage, description=description)
    parser.add_argument('range', help='git commit range to use')
    parser.add_argument('stacktrace', help='stacktrace filename')
    args = parser.parse_args()

    extracted = parse_trace.extract_python_traceback_from_file(args.stacktrace)

    parse_trace.print_traceback(extracted)

    trace_files = set()
    trace_snippets = set()
    for f, line, function, code in extracted:
        trace_files.add(f)
        trace_snippets.add(code)

    highlighted_code_commits = collections.defaultdict(list)
    for snippet in trace_snippets:
        commits = git.pickaxe(snippet, args.range)
        for commit in commits:
            highlighted_code_commits[commit].append(snippet)

    print ""
    print ""
    print "Commits touching code snippets:"
    print ""
    for k, v in highlighted_code_commits.iteritems():
        git.print_one_commit(k, oneline=True)
        print "Files:"
        for f in v:
            print " * %s" % f
        print ""

    commit_files = git.files_touched(args.range)
    highlighted_file_commits = lookup_file(commit_files, trace_files)
    print ""
    print ""
    print "Commits touching related files:"
    print ""
    for k, v in highlighted_file_commits.iteritems():
        git.print_one_commit(k, oneline=True)
        print "Files:"
        for f in v:
            print " * %s" % f
        print ""

if __name__ == "__main__":
    main()

from git_stacktrace import git


class Result(object):
    """Track matches to stacktrace in a given commit."""

    def __init__(self, commit):
        self._commit = commit
        self.files_modified = set()
        self.files_deleted = set()
        self.files_added = set()
        self.lines_added = set()
        self.lines_removed = set()
        self._line_numbers_matched = 0

    @property
    def commit(self):
        return self._commit

    def add_file(self, git_file, line_number=None):
        if line_number:
            self._line_numbers_matched += 1
            filename = git_file.filename + ":" + str(line_number)
        else:
            filename = git_file.filename
        if git_file.state in [git.GitFile.ADDED, git.GitFile.COPY_EDIT]:
            self.files_added.add(filename)
        elif git_file.state in [git.GitFile.DELETED]:
            self.files_deleted.add(filename)
        else:
            self.files_modified.add(filename)

    def __hash__(self):
        return hash(self.commit)

    def __str__(self):
        result = ""
        result += git.format_one_commit(self.commit) + '\n'
        if len(self.files_added) > 0:
            result += "Files Added:\n"
        for f in self.files_added:
            result += "    - %s\n" % f
        if len(self.files_modified) > 0:
            result += "Files Modified:\n"
        for f in self.files_modified:
            result += "    - %s\n" % f
        if len(self.files_deleted) > 0:
            result += "Files Deleted:\n"
        for f in self.files_deleted:
            result += "    - %s\n" % f
        if len(self.lines_added) > 0:
            result += "Lines Added:\n"
        for line in self.lines_added:
            result += '    - "%s"\n' % line
        if len(self.lines_removed) > 0:
            result += "Lines Removed:\n"
        for line in self.lines_removed:
            result += '    - "%s"\n' % line
        return result

    def __iter__(self):
        custom, full, url = git.get_commit_info(self.commit, color=False)
        yield 'commit', self.commit
        yield 'custom', custom
        yield 'full', full
        yield 'url', url
        yield 'files_added', list(self.files_added)
        yield 'files_modified', list(self.files_modified)
        yield 'files_deleted', list(self.files_deleted)
        yield 'lines_added', list(self.lines_added)
        yield 'lines_removed', list(self.lines_removed)

    def rank(self):
        return (len(self.files_modified) + len(self.files_deleted)*2 + len(self.files_added)*3 +
                len(self.lines_added)*3 + len(self.lines_removed)*2 + self._line_numbers_matched*4)


class Results(object):
    """List of results."""

    def __init__(self):
        self.results = {}

    def get_result(self, commit):
        if commit not in self.results:
            self.results[commit] = Result(commit)
        return self.results[commit]

    def get_sorted_results(self):
        """Return list of results sorted by rank"""
        results = self.results.values()
        return sorted(results, key=lambda r: r.rank(), reverse=True)

    def get_sorted_results_by_dict(self):
        """Return a list of dictionaries of the results sorted by rank"""
        results = self.get_sorted_results()
        return [dict(r) for r in results]

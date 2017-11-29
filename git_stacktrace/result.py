from git_stacktrace import git


class Result(object):
    """Track matches to stacktrace in a given commit."""

    def __init__(self, commit):
        self.__commit = commit
        self.files_modified = set()
        self.files_deleted = set()
        self.files_added = set()
        self.lines_added = set()
        self.lines_removed = set()
        self._line_numbers_matched = 0
        self.__commit_info_fetched = False

    def _lazy_fetch(self):
        if not self.__commit_info_fetched:
            self.__info = git.get_commit_info(self.commit, color=False)
            self.__commit_info_fetched = True

    @property
    def commit(self):
        """git commit hash"""
        return self.__commit

    @property
    def summary(self):
        """pre-formatted summary of git commit information"""
        self._lazy_fetch()
        return self.__info.summary

    @property
    def subject(self):
        """commit subject"""
        self._lazy_fetch()
        return self.__info.subject

    @property
    def body(self):
        """body of commit message"""
        self._lazy_fetch()
        return self.__info.body

    @property
    def url(self):
        """url found in commit body"""
        self._lazy_fetch()
        return self.__info.url

    @property
    def author(self):
        """commit author"""
        self._lazy_fetch()
        return self.__info.author

    @property
    def date(self):
        """commit date (not author date)"""
        self._lazy_fetch()
        return self.__info.date

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
        for f in sorted(self.files_added):
            result += "    - %s\n" % f

        if len(self.files_modified) > 0:
            result += "Files Modified:\n"
        for f in sorted(self.files_modified):
            result += "    - %s\n" % f

        if len(self.files_deleted) > 0:
            result += "Files Deleted:\n"
        for f in sorted(self.files_deleted):
            result += "    - %s\n" % f

        if len(self.lines_added) > 0:
            result += "Lines Added:\n"
        for line in sorted(self.lines_added):
            result += '    - "%s"\n' % line

        if len(self.lines_removed) > 0:
            result += "Lines Removed:\n"
        for line in sorted(self.lines_removed):
            result += '    - "%s"\n' % line
        return result

    def __iter__(self):
        self._lazy_fetch()
        yield 'commit', self.commit
        yield 'summary', self.summary
        yield 'subject', self.subject
        yield 'body', self.body
        yield 'url', self.url
        yield 'author', self.author
        yield 'date', self.date
        yield 'files_added', list(self.files_added)
        yield 'files_modified', list(self.files_modified)
        yield 'files_deleted', list(self.files_deleted)
        yield 'lines_added', list(self.lines_added)
        yield 'lines_removed', list(self.lines_removed)

    def rank(self):
        return (len(self.files_modified) + len(self.files_deleted)*2 + len(self.files_added)*3 +
                len(self.lines_added)*3 + len(self.lines_removed)*2 + self._line_numbers_matched*4)

    def __eq__(self, other):
        return self.commit == other.commit

    def __lt__(self, other):
        if self.rank() == other.rank():
            # Make sorted order deterministic (but random) if rank is same
            # TODO fall back to sorting chronologically
            return self.commit < other.commit
        return self.rank() < other.rank()


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
        return sorted(results, reverse=True)

    def get_sorted_results_by_dict(self):
        """Return a list of dictionaries of the results sorted by rank"""
        results = self.get_sorted_results()
        return [dict(r) for r in results]

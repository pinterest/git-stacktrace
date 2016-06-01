class Result(object):
    """Track matches to stacktrace in a given commit."""

    def __init__(self, commit):
        self._commit = commit
        self.files = set()
        self.lines_added = set()
        self.lines_removed = set()

    @property
    def commit(self):
        return self._commit

    def __hash__(self):
        return self.commit.__hash__()

    def __str__(self):
        result = ""
        if len(self.files) > 0:
            result += "files:\n"
        for f in self.files:
            result += "    - %s\n" % f
        if len(self.lines_added) > 0:
            result += "lines added:\n"
        for line in self.lines_added:
            result += '    - "%s"\n' % line
        if len(self.lines_removed) > 0:
            result += "lines removed:\n"
        for line in self.lines_removed:
            result += '    - "%s"\n' % line

        return result

    def rank(self):
        return len(self.files) + len(self.lines_added)*3 + len(self.lines_removed)*2


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

class Result(object):
    """Track matches to stacktrace in a given commit."""

    def __init__(self, commit):
        self._commit = commit
        self.files = set()
        self.snippets = set()

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
        if len(self.snippets) > 0:
            result += "code:\n"
        for snippet in self.snippets:
            result += '    - "%s"\n' % snippet

        return result


class Results(object):
    """List of results."""

    def __init__(self):
        self.results = {}

    def get_result(self, commit):
        if commit not in self.results:
            self.results[commit] = Result(commit)
        return self.results[commit]

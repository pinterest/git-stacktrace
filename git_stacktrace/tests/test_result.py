import testtools

from git_stacktrace.tests import base
from git_stacktrace import result


class TestResult(base.TestCase):
    commit_hash = 'hash1'

    def test_init_result(self):
        commit1 = result.Result(self.commit_hash)
        self.assertEqual(commit1.commit, self.commit_hash)
        with testtools.ExpectedException(AttributeError):
            commit1.commit = 'test'

    def test_files(self):
        commit1 = result.Result(self.commit_hash)
        expected_files = set(['file1', 'file2'])
        commit1.files.add('file1')
        commit1.files.add('file1')
        commit1.files.add('file2')
        self.assertEqual(commit1.files, expected_files)

    def test_lines(self):
        commit1 = result.Result(self.commit_hash)
        expected_lines_added = set(['pass', '1+1'])
        expected_lines_removed = set(['1+2'])
        commit1.lines_added.add('pass')
        commit1.lines_added.add('pass')
        commit1.lines_added.add('1+1')
        self.assertEqual(commit1.lines_added, expected_lines_added)
        commit1.lines_removed.add('1+2')
        commit1.lines_removed.add('1+2')
        self.assertEqual(commit1.lines_removed, expected_lines_removed)

    def test_str(self):
        commit1 = result.Result(self.commit_hash)
        commit1.files.add('file1')
        expected = "files:\n    - file1\n"
        self.assertEqual(str(commit1), expected)
        commit1.lines_added.add('pass')
        expected = "files:\n    - file1\nlines added:\n    - \"pass\"\n"
        commit1.lines_removed.add('True')
        expected = "files:\n    - file1\nlines added:\n    - \"pass\"\nlines removed:\n    - \"True\"\n"
        self.assertEqual(str(commit1), expected)

    def test_rank(self):
        commit1 = result.Result(self.commit_hash)
        self.assertEqual(commit1.rank(), 0)
        commit1.files.add('file1')
        self.assertEqual(commit1.rank(), 1)
        commit1.lines_added.add('pass')
        self.assertEqual(commit1.rank(), 4)


class TestResults(base.TestCase):

    def test_results(self):
        results = result.Results()
        commit1 = results.get_result('hash1')
        commit1.files.add('file1')
        commit2 = results.get_result('hash1')
        self.assertEquals(commit1, commit2)

    def test_sorted_results(self):
        results = result.Results()
        commit2 = results.get_result('hash2')
        commit1 = results.get_result('hash1')
        commit1.files.add('file1')
        expected = [commit1, commit2]
        self.assertEquals(results.get_sorted_results(), expected)

    def test_sorted_results_inverse(self):
        results = result.Results()
        commit1 = results.get_result('hash1')
        commit1.files.add('file1')
        commit2 = results.get_result('hash2')
        expected = [commit1, commit2]
        self.assertEquals(results.get_sorted_results(), expected)

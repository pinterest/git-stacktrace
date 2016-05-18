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

    def test_snippets(self):
        commit1 = result.Result(self.commit_hash)
        expected_snippets = set(['pass', '1+1'])
        commit1.snippets.add('pass')
        commit1.snippets.add('pass')
        commit1.snippets.add('1+1')
        self.assertEqual(commit1.snippets, expected_snippets)

    def test_str(self):
        commit1 = result.Result(self.commit_hash)
        commit1.files.add('file1')
        expected = "files:\n    - file1\n"
        self.assertEqual(str(commit1), expected)
        commit1.snippets.add('pass')
        expected = "files:\n    - file1\ncode:\n    - \"pass\"\n"
        self.assertEqual(str(commit1), expected)

    def test_rank(self):
        commit1 = result.Result(self.commit_hash)
        self.assertEqual(commit1.rank(), 0)
        commit1.files.add('file1')
        self.assertEqual(commit1.rank(), 1)
        commit1.snippets.add('pass')
        self.assertEqual(commit1.rank(), 3)


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

import mock
import testtools

from git_stacktrace.tests import base
from git_stacktrace import result


class TestResult(base.TestCase):
    commit_hash = 'hash1'

    def test_init_result(self):
        commit1 = result.Result(self.commit_hash)
        self.assertEqual(self.commit_hash, commit1.commit)
        with testtools.ExpectedException(AttributeError):
            commit1.commit = 'test'

    def test_files(self):
        commit1 = result.Result(self.commit_hash)
        expected_files = set(['file1', 'file2'])
        commit1.files.add('file1')
        commit1.files.add('file1')
        commit1.files.add('file2')
        self.assertEqual(expected_files, commit1.files)

    def test_lines(self):
        commit1 = result.Result(self.commit_hash)
        expected_lines_added = set(['pass', '1+1'])
        expected_lines_removed = set(['1+2'])
        commit1.lines_added.add('pass')
        commit1.lines_added.add('pass')
        commit1.lines_added.add('1+1')
        self.assertEqual(expected_lines_added, commit1.lines_added)
        commit1.lines_removed.add('1+2')
        commit1.lines_removed.add('1+2')
        self.assertEqual(expected_lines_removed, commit1.lines_removed)

    @mock.patch('git_stacktrace.git.get_commit_info')
    def test_str(self, mocked_git_info):
        mocked_git_info.return_value = "custom", "full", "url"
        commit1 = result.Result(self.commit_hash)
        commit1.files.add('file1')
        expected = "custom\nLink:        url\nFiles:\n    - file1\n"
        self.assertEqual(expected, str(commit1))
        commit1.lines_added.add('pass')
        expected = "custom\nLink:        url\nFiles:\n    - file1\nLines Added:\n    - \"pass\"\n"
        commit1.lines_removed.add('True')
        expected = ("custom\nLink:        url\nFiles:\n    - file1\nLines Added:\n    - \"pass\"\nLines "
                    "Removed:\n    - \"True\"\n")
        self.assertEqual(expected, str(commit1))

    @mock.patch('git_stacktrace.git.get_commit_info')
    def test_str_no_url(self, mocked_git_info):
        mocked_git_info.return_value = "custom", "full", None
        commit1 = result.Result(self.commit_hash)
        commit1.files.add('file1')
        expected = "custom\nFiles:\n    - file1\n"
        self.assertEqual(expected, str(commit1))
        commit1.lines_added.add('pass')
        expected = "custom\nFiles:\n    - file1\nLines Added:\n    - \"pass\"\n"
        commit1.lines_removed.add('True')
        expected = ("custom\nFiles:\n    - file1\nLines Added:\n    - \"pass\"\nLines "
                    "Removed:\n    - \"True\"\n")
        self.assertEqual(expected, str(commit1))

    def test_rank(self):
        commit1 = result.Result(self.commit_hash)
        self.assertEqual(0, commit1.rank())
        commit1.files.add('file1')
        self.assertEqual(1, commit1.rank())
        commit1.lines_added.add('pass')
        self.assertEqual(4, commit1.rank())

    @mock.patch('git_stacktrace.git.get_commit_info')
    def test_dict(self, mocked_git_info):
        mocked_git_info.return_value = "custom", "full", "url"
        commit1 = result.Result(self.commit_hash)
        commit1.files.add('file1')
        commit1.lines_removed.add('True')
        commit1.lines_added.add('pass')
        expected = {
                    'commit': 'hash1',
                    'files': ['file1'],
                    'full': 'full',
                    'lines_added': ['pass'],
                    'lines_removed': ['True'],
                    'custom': 'custom',
                    'url': 'url'}
        self.assertEqual(expected, dict(commit1))


class TestResults(base.TestCase):

    def test_results(self):
        results = result.Results()
        commit1 = results.get_result('hash1')
        commit1.files.add('file1')
        commit2 = results.get_result('hash1')
        self.assertEqual(commit1, commit2)

    def test_sorted_results(self):
        results = result.Results()
        commit2 = results.get_result('hash2')
        commit1 = results.get_result('hash1')
        commit1.files.add('file1')
        expected = [commit1, commit2]
        self.assertEqual(expected, results.get_sorted_results())

    def test_sorted_results_inverse(self):
        results = result.Results()
        commit1 = results.get_result('hash1')
        commit1.files.add('file1')
        commit2 = results.get_result('hash2')
        expected = [commit1, commit2]
        self.assertEqual(expected, results.get_sorted_results())

    @mock.patch('git_stacktrace.git.get_commit_info')
    def test_get_sorted_results_by_dict(self, mocked_git_info):
        mocked_git_info.return_value = "custom", "full", "url"
        results = result.Results()
        commit2 = results.get_result('hash2')
        commit1 = results.get_result('hash1')
        commit1.files.add('file1')
        expected = [dict(commit1), dict(commit2)]
        self.assertEqual(expected, results.get_sorted_results_by_dict())

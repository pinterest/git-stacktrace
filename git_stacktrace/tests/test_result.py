import mock
import testtools

from git_stacktrace.tests import base
from git_stacktrace import git
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
        expected_files_modified = set(['file1:10', 'file1'])
        expected_files_added = set(['file2', 'file3'])
        expected_files_deleted = set(['file4'])
        commit1.add_file(git.GitFile('file1', 'M'), line_number=10)
        commit1.add_file(git.GitFile('file1', 'M'))
        commit1.add_file(git.GitFile('file2', 'A'))
        commit1.add_file(git.GitFile('file3', 'C'))
        commit1.add_file(git.GitFile('file4', 'D'))
        self.assertEqual(expected_files_modified, commit1.files_modified)
        self.assertEqual(expected_files_added, commit1.files_added)
        self.assertEqual(expected_files_deleted, commit1.files_deleted)

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
        commit1.add_file(git.GitFile('file1', 'M'))
        expected = "custom\nLink:        url\nFiles Modified:\n    - file1\n"
        commit1.add_file(git.GitFile('file2', 'A'))
        expected = "custom\nLink:        url\nFiles Added:\n    - file2\nFiles Modified:\n    - file1\n"
        self.assertEqual(expected, str(commit1))
        commit1.lines_added.add('pass')
        expected = ("custom\nLink:        url\nFiles Added:\n    - file2\nFiles Modified:\n    - "
                    "file1\nLines Added:\n    - \"pass\"\n")
        commit1.lines_removed.add('True')
        expected = ("custom\nLink:        url\nFiles Added:\n    - file2\nFiles Modified:\n    - "
                    "file1\nLines Added:\n    - \"pass\"\nLines Removed:\n    - \"True\"\n")
        commit1.add_file(git.GitFile('file3', 'D'), line_number=11)
        expected = ("custom\nLink:        url\nFiles Added:\n    - file2\nFiles Modified:\n    - "
                    "file1\nFiles Deleted:\n    - file3:11\nLines Added:\n    - "
                    "\"pass\"\nLines Removed:\n    - \"True\"\n")
        self.assertEqual(expected, str(commit1))

    @mock.patch('git_stacktrace.git.get_commit_info')
    def test_str_no_url(self, mocked_git_info):
        mocked_git_info.return_value = "custom", "full", None
        commit1 = result.Result(self.commit_hash)
        commit1.add_file(git.GitFile('file1', 'M'))
        expected = "custom\nFiles Modified:\n    - file1\n"
        self.assertEqual(expected, str(commit1))
        commit1.lines_added.add('pass')
        expected = "custom\nFiles Modified:\n    - file1\nLines Added:\n    - \"pass\"\n"
        commit1.lines_removed.add('True')
        expected = ("custom\nFiles Modified:\n    - file1\nLines Added:\n    - \"pass\"\nLines "
                    "Removed:\n    - \"True\"\n")
        self.assertEqual(expected, str(commit1))

    def test_rank(self):
        commit1 = result.Result(self.commit_hash)
        self.assertEqual(0, commit1.rank())
        commit1.add_file(git.GitFile('file1', 'M'))
        self.assertEqual(1, commit1.rank())
        commit1.add_file(git.GitFile('file2', 'A'))
        self.assertEqual(4, commit1.rank())
        commit1.lines_added.add('pass')
        self.assertEqual(7, commit1.rank())
        commit1.add_file(git.GitFile('file3', 'M'), line_number=12)
        self.assertEqual(12, commit1.rank())

    @mock.patch('git_stacktrace.git.get_commit_info')
    def test_dict(self, mocked_git_info):
        mocked_git_info.return_value = "custom", "full", "url"
        commit1 = result.Result(self.commit_hash)
        commit1.add_file(git.GitFile('file1', 'M'))
        commit1.add_file(git.GitFile('file2', 'A'), line_number=12)
        commit1.add_file(git.GitFile('file3', 'D'))
        commit1.lines_removed.add('True')
        commit1.lines_added.add('pass')
        expected = {
                    'commit': 'hash1',
                    'files_added': ['file2:12'],
                    'files_modified': ['file1'],
                    'files_deleted': ['file3'],
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
        commit1.add_file(git.GitFile('file1', 'A'))
        commit2 = results.get_result('hash1')
        self.assertEqual(commit1, commit2)

    def test_sorted_results(self):
        results = result.Results()
        commit2 = results.get_result('hash2')
        commit1 = results.get_result('hash1')
        commit1.add_file(git.GitFile('file1', 'M'))
        expected = [commit1, commit2]
        self.assertEqual(expected, results.get_sorted_results())

    def test_sorted_results_inverse(self):
        results = result.Results()
        commit1 = results.get_result('hash1')
        commit1.add_file(git.GitFile('file1', 'M'))
        commit2 = results.get_result('hash2')
        expected = [commit1, commit2]
        self.assertEqual(expected, results.get_sorted_results())

    @mock.patch('git_stacktrace.git.get_commit_info')
    def test_get_sorted_results_by_dict(self, mocked_git_info):
        mocked_git_info.return_value = "custom", "full", "url"
        results = result.Results()
        commit2 = results.get_result('hash2')
        commit1 = results.get_result('hash1')
        commit1.add_file(git.GitFile('file1', 'M'))
        expected = [dict(commit1), dict(commit2)]
        self.assertEqual(expected, results.get_sorted_results_by_dict())

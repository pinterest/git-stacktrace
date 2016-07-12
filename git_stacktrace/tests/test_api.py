import mock

from git_stacktrace.tests import base
from git_stacktrace import api


class TestApi(base.TestCase):

    @mock.patch('git_stacktrace.git.convert_since')
    def test_convert_since(self, mocked_command):
        expected = "HASH1..HASH2"
        mocked_command.return_value = expected
        self.assertEquals(expected, api.convert_since('1.day'))

    @mock.patch('git_stacktrace.git.valid_range')
    def test_valid_range(self, mocked_command):
        expected = True
        mocked_command.return_value = expected
        self.assertEquals(expected, api.valid_range('hash1..hash2'))

        expected = False
        mocked_command.return_value = expected
        self.assertEquals(expected, api.valid_range('hash1..hash2'))

    def get_traceback(self):
        with open('git_stacktrace/tests/examples/trace3') as f:
            traceback = api.Traceback(f.readlines())
        return traceback

    def setup_mocks(self, mock_files, mock_files_touched):
        mock_files_touched.return_value = {'hash2': ['common/utils/geo_utils.py']}
        mock_files.return_value = ['common/utils/geo_utils.py']

    @mock.patch('git_stacktrace.git.pickaxe')
    @mock.patch('git_stacktrace.git.files_touched')
    @mock.patch('git_stacktrace.git.files')
    def test_lookup_stacktrace(self, mock_files, mock_files_touched, mock_pickaxe):
        traceback = self.get_traceback()
        self.setup_mocks(mock_files, mock_files_touched)
        api.lookup_stacktrace(traceback, "hash1..hash3", fast=False)
        self.assertEqual(3, mock_pickaxe.call_count)

    @mock.patch('git_stacktrace.git.pickaxe')
    @mock.patch('git_stacktrace.git.files_touched')
    @mock.patch('git_stacktrace.git.files')
    def test_lookup_stacktrace_fast(self, mock_files, mock_files_touched, mock_pickaxe):
        traceback = self.get_traceback()
        self.setup_mocks(mock_files, mock_files_touched)
        api.lookup_stacktrace(traceback, "hash1..hash3", fast=True)
        self.assertEqual(1, mock_pickaxe.call_count)

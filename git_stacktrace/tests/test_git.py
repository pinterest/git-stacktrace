import mock

from git_stacktrace.tests import base
from git_stacktrace import git


class TestParseStacktrace(base.TestCase):
    @mock.patch('git_stacktrace.git.run_command')
    def test_convert_since_fail(self, mocked_command):
        mocked_command.return_value = ""
        self.assertRaises(Exception, git.convert_since, '1.day')

    @mock.patch('git_stacktrace.git.run_command')
    def test_convert_since(self, mocked_command):
        mocked_command.return_value = '\n'.join(["de75c8dd27af30daef012a9902af4c39c4728710",
                                                 "04a13ace3a3e490a5e1a74aae740f45fee6562c3",
                                                 "c0497475799306eebcfd014657150daa9af9c488",
                                                 "f301b355050f64ebc2e83ebffc583713113aee9b",
                                                 "32eba9e2c389c427c5b7b2288353eaf0903d52c0"])
        expected = "32eba9e2c389c427c5b7b2288353eaf0903d52c0..de75c8dd27af30daef012a9902af4c39c4728710"
        self.assertEqual(expected, git.convert_since('1.day'))

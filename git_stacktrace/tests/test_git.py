import mock

from git_stacktrace.tests import base
from git_stacktrace import git
from git_stacktrace import parse_trace


class TestGitFile(base.TestCase):

    def test_git_file(self):
        git_file = git.GitFile("file1", "M")
        self.assertEqual(git_file.filename, "file1")
        self.assertEqual(git_file.state, git.GitFile.MODIFIED)
        git_file = git.GitFile("file2", "A")
        self.assertEqual(git_file.filename, "file2")
        self.assertEqual(git_file.state, git.GitFile.ADDED)

    def test_git_file_invalid(self):
        self.assertRaises(Exception, git.GitFile, "file1", "x")

    def test_git_file_cmp(self):
        git_file1 = git.GitFile("file1", "M")
        git_file = git.GitFile("file1", "A")
        self.assertEqual(git_file, git_file1)
        self.assertEqual(git_file, u"file1")
        self.assertEqual(git_file, "file1")


class TestGit(base.TestCase):
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

    @mock.patch('git_stacktrace.git.run_command')
    def test_files_touched(self, mocked_command):
        mocked_command.return_value = '\n'.join([
            "1ca8dd2b178ef8f308849bac2b0eaecaf91abc70",
            "",
            ":100644 100644 bcd1234... 0123456... M	file0",
            ":100644 100644 abcd123... 1234567... C68	file1	file2",
            ":100644 100644 abcd123... 1234567... R86	file1	file3",
            ":000000 100644 0000000... 1234567... A	file4 space/log",
            ":100644 100644 f9731ae1d4... 6dc2860... M       test/file"
            ":100644 000000 1234567... 0000000... D	file5"])
        expected = {"1ca8dd2b178ef8f308849bac2b0eaecaf91abc70": ["file0", "file2", "file3", "file4 space/log", "file5"]}
        self.assertEqual(expected, git.files_touched("A..B"))

    @mock.patch('git_stacktrace.git.run_command')
    def test_line_match(self, mocked_command):
        mocked_command.return_value = '\n'.join([
            "diff --git a/test_api.py b/test_api.py",
            "index 73e79d1..884b953 100644",
            "--- a/test_api.py",
            "+++ b/test_api.py",
            "@@ -35,7 +35,9 @@ class TestApi(base.TestCase):",
            "     @mock.patch('git_stacktrace.git.pickaxe')",
            "     @mock.patch('git_stacktrace.git.files_touched')",
            "     @mock.patch('git_stacktrace.git.files')",
            "-    def test_lookup_stacktrace(self, mock_files, mock_files_touched, mock_pickaxe):",
            "+    @mock.patch('git_stacktrace.git.line_match')",
            "+    def test_lookup_stacktrace(self, mock_line_match, mock_files, mock_files_touched, mock_pickaxe):",
            "+        mock_files_touched.return_value = True",
            "         traceback = self.get_traceback()",
            "         self.setup_mocks(mock_files, mock_files_touched)",
        ])
        filename = "test_api.py"
        line = parse_trace.Line(filename, 38, None, None)
        line.git_filename = filename
        self.assertTrue(git.line_match("hash1", line))
        line.line_number = 5
        self.assertFalse(git.line_match("hash1", line))

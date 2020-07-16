import mock

from git_stacktrace.tests import base
from git_stacktrace.server import Args


class TestApi(base.TestCase):
    def test_default_args(self):
        args = Args({})
        self.assertEqual("", args.trace)
        self.assertEqual("", args.branch)
        self.assertFalse(args.fast)

    def test_args_from_json(self):
        json = '{"branch": "master", "fast": "on"}'
        args = Args.from_json_body(json)
        self.assertEqual("", args.trace)
        self.assertEqual("master", args.branch)
        self.assertTrue(args.fast)

    def test_args_from_json_as_array_vals(self):
        json = '{"branch": ["master"], "fast": ["on"]}'
        args = Args.from_json_body(json)
        self.assertEqual("master", args.branch)
        self.assertTrue(args.fast)

    def test_args_from_querystring(self):
        qs = "?branch=master&fast=on"
        args = Args.from_qs(qs)
        self.assertEqual("", args.trace)
        self.assertEqual("master", args.branch)
        self.assertTrue(args.fast)

    def test_args_from_querystring_without_qmark(self):
        qs = "branch=master&fast=on"
        args = Args.from_qs(qs)
        self.assertEqual("master", args.branch)

    def test_args_from_querystring_multiple_vals(self):
        qs = "?branch=master&branch=feature"
        args = Args.from_qs(qs)
        self.assertEqual("master", args.branch)

    def test_unescape_args(self):
        qs = "?branch=origin%2Fmaster&fast=on"
        args = Args.from_qs(qs)
        self.assertEqual("origin/master", args.branch)

    def test_args_ok_when_empty(self):
        args = Args({})
        self.assertIsNone(args.validate())

    def test_args_message_for_invalid_optionType(self):
        args = Args({"option-type": "foo"})
        self.assertIn("Invalid `type` value", args.validate())

    def test_args_byDate_requires_since(self):
        args = Args({"option-type": "by-date"})
        self.assertIn("Missing `since` value", args.validate())

    @mock.patch("git_stacktrace.server.api.convert_since")
    @mock.patch("git_stacktrace.server.api.valid_range")
    def test_args_byDate_errors_on_invalid_range(self, mock_valid_range, mock_convert_since):
        mock_valid_range.return_value = False
        args = Args({"option-type": "by-date", "since": "1.day"})
        self.assertIn("Found no commits in", args.validate())

    @mock.patch("git_stacktrace.server.api.convert_since")
    @mock.patch("git_stacktrace.server.api.valid_range")
    def test_args_byDate_returns_none_for_good_range(self, mock_valid_range, mock_convert_since):
        mock_valid_range.return_value = True
        args = Args({"option-type": "by-date", "since": "1.day"})
        self.assertIsNone(args.validate())

    @mock.patch("git_stacktrace.server.api.valid_range")
    def test_args_byRange_errors_on_invalid_range(self, mock_valid_range):
        mock_valid_range.return_value = False
        args = Args({"option-type": "by-range"})
        self.assertIn("Found no commits in", args.validate())

    @mock.patch("git_stacktrace.server.api.valid_range")
    def test_args_byRange_returns_none_for_good_range(self, mock_valid_range):
        mock_valid_range.return_value = True
        args = Args({"option-type": "by-range"})
        self.assertIsNone(args.validate())

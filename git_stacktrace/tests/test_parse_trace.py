"""
test_git_stacktrace
----------------------------------
Tests for `git_stacktrace` module.
"""
import glob

from git_stacktrace.tests import base
from git_stacktrace import parse_trace


class TestParseStacktrace(base.TestCase):
    trace3_expected = [
            ('../common/utils/geo_utils.py', 68, 'get_ip_geo', 'return get_geo_db().record_by_addr(ip_address)'),
            ('/mnt/virtualenv_A/local/lib/python2.7/site-packages/pygeoip/__init__.py', 563,
                'record_by_addr', 'ipnum = util.ip2long(addr)'),
            ('/mnt/virtualenv_A/local/lib/python2.7/site-packages/pygeoip/util.py', 36, 'ip2long',
                'return int(binascii.hexlify(socket.inet_pton(socket.AF_INET6, ip)), 16)')]

    def test_extract_traceback_from_file(self):
        # extract_python_traceback_from_file will raise an exception if it incorrectly parses a file
        for filename in glob.glob('git_stacktrace/tests/examples/trace*'):
            extracted = parse_trace.extract_python_traceback_from_file(filename)
            if filename == 'git_stacktrace/tests/examples/trace3':
                self.assertEqual(extracted, self.trace3_expected)

    def test_filter_site_packages(self):
        self.assertEqual(
                parse_trace.filter_site_packages(self.trace3_expected),
                [('../common/utils/geo_utils.py', 68, 'get_ip_geo', 'return get_geo_db().record_by_addr(ip_address)')])

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
            traceback = parse_trace.Traceback(filename=filename, filter_site_packages=False)
            if filename == 'git_stacktrace/tests/examples/trace3':
                self.assertEqual(traceback.traceback_format(), self.trace3_expected)

    def test_filter_site_packages(self):
        self.assertEqual(
                parse_trace.Traceback(filename='git_stacktrace/tests/examples/trace3',
                                      filter_site_packages=True).traceback_format(),
                [('../common/utils/geo_utils.py', 68, 'get_ip_geo', 'return get_geo_db().record_by_addr(ip_address)')])


class TestLine(base.TestCase):
    def test_line(self):
        line_data = ("./file", 1, 'foo', 'pass')
        line = parse_trace.Line(*line_data)
        line.git_filename = "file"
        self.assertEqual(line.traceback_format(), line_data)

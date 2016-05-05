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
            with open(filename) as f:
                traceback = parse_trace.Traceback(f.readlines(), filter_site_packages=False)
                if filename == 'git_stacktrace/tests/examples/trace3':
                    self.assertEqual(self.trace3_expected, traceback.traceback_format())

    def test_filter_site_packages(self):
        with open('git_stacktrace/tests/examples/trace3') as f:
            self.assertEqual(
                             [('../common/utils/geo_utils.py', 68, 'get_ip_geo',
                               'return get_geo_db().record_by_addr(ip_address)')],
                             parse_trace.Traceback(f.readlines(), filter_site_packages=True).traceback_format(),
                 )

    def test_str(self):
        expected = ('  File "../common/utils/geo_utils.py", line 68, in get_ip_geo\n'
                    '    return get_geo_db().record_by_addr(ip_address)\n')
        with open('git_stacktrace/tests/examples/trace3') as f:
            self.assertEqual(
                    expected,
                    str(parse_trace.Traceback(f.readlines(), filter_site_packages=True)))


class TestLine(base.TestCase):
    def test_line(self):
        line_data = ("./file", 1, 'foo', 'pass')
        line = parse_trace.Line(*line_data)
        line.git_filename = "file"
        self.assertEqual(line_data, line.traceback_format())

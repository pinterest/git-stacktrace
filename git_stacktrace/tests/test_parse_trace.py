import glob

from git_stacktrace.tests import base
from git_stacktrace import parse_trace


class TestParsePythonStacktrace(base.TestCase):
    trace3_expected = [
            ('../common/utils/geo_utils.py', 68, 'get_ip_geo', 'return get_geo_db().record_by_addr(ip_address)'),
            ('/mnt/virtualenv_A/local/lib/python2.7/site-packages/pygeoip/__init__.py', 563,
                'record_by_addr', 'ipnum = util.ip2long(addr)'),
            ('/mnt/virtualenv_A/local/lib/python2.7/site-packages/pygeoip/util.py', 36, 'ip2long',
                'return int(binascii.hexlify(socket.inet_pton(socket.AF_INET6, ip)), 16)')]

    def get_trace(self, number=3):
        with open('git_stacktrace/tests/examples/python%d.trace' % number) as f:
            trace = parse_trace.PythonTraceback(f.readlines())
        return trace

    def test_extract_traceback_from_file(self):
        # extract_python_traceback_from_file will raise an exception if it incorrectly parses a file
        for filename in glob.glob('git_stacktrace/tests/examples/python*.trace'):
            with open(filename) as f:
                traceback = parse_trace.PythonTraceback(f.readlines())
                if filename == 'git_stacktrace/tests/examples/python3.trace':
                    self.assertEqual(self.trace3_expected, traceback.traceback_format())

    def test_str(self):
        with open('git_stacktrace/tests/examples/python3.trace') as f:
            expected = f.read()
        trace = self.get_trace()
        self.assertEqual(expected, str(trace))
        with open('git_stacktrace/tests/examples/python5.trace') as f:
            expected = f.read()
        trace = self.get_trace(number=5)
        self.assertEqual(expected, str(trace))
        with open('git_stacktrace/tests/examples/python6.trace') as f:
            expected = f.read()
        trace = self.get_trace(number=6)
        self.assertEqual(expected, str(trace))

    def test_exception(self):
        self.assertRaises(parse_trace.ParseException, parse_trace.PythonTraceback, "NOT A TRACEBACK")
        with open('git_stacktrace/tests/examples/java.trace') as f:
            self.assertRaises(parse_trace.ParseException, parse_trace.PythonTraceback, f.readlines())

    def test_file_match(self):
        trace = self.get_trace()
        self.assertTrue(trace.file_match(trace.lines[0].trace_filename, ['common/utils/geo_utils.py']))
        self.assertFalse(trace.file_match(trace.lines[0].trace_filename, ['common/utils/fake.py']))


class TestParseJavaStacktrace(base.TestCase):

    def get_trace(self):
        with open('git_stacktrace/tests/examples/java.trace') as f:
            trace = parse_trace.JavaTraceback(f.readlines())
        return trace

    def test_str(self):
        with open('git_stacktrace/tests/examples/java.trace') as f:
            expected = f.read()
        trace = self.get_trace()
        self.assertEqual(expected, str(trace))

    def test_extract_traceback(self):
        trace = self.get_trace()
        line = trace.lines[1]
        self.assertEqual(106, line.line_number)
        self.assertEqual('java/io/FileInputStream.java', line.trace_filename)
        self.assertEqual('FileInputStream', line.class_name)
        line = trace.lines[2]
        self.assertEqual(15, line.line_number)
        self.assertEqual('com/devdaily/tests/ExceptionTest.java', line.trace_filename)
        self.assertEqual('ExceptionTest', line.class_name)

    def test_exception(self):
        self.assertRaises(parse_trace.ParseException, parse_trace.JavaTraceback, "NOT A TRACEBACK")
        for filename in glob.glob('git_stacktrace/tests/examples/python*.trace'):
            with open(filename) as f:
                self.assertRaises(parse_trace.ParseException, parse_trace.JavaTraceback, f.readlines())

    def test_file_match(self):
        trace = self.get_trace()
        self.assertTrue(trace.file_match(trace.lines[2].trace_filename,
                        ['src/main/java/com/devdaily/tests/ExceptionTest.java']))
        self.assertFalse(trace.file_match(trace.lines[2].trace_filename,
                         ['src/main/java/com/devdaily/tests/Fake.java']))


class TestLine(base.TestCase):
    def test_line(self):
        line_data = ("./file", 1, 'foo', 'pass')
        line = parse_trace.Line(*line_data)
        line.git_filename = "file"
        self.assertEqual(line_data, line.traceback_format())


class TestParseTrace(base.TestCase):
    def test_parse_trace(self):
        for filename in glob.glob('git_stacktrace/tests/examples/*.trace'):
            with open(filename) as f:
                parse_trace.parse_trace(f.readlines())

"""Extract important filenames, lines, functions and code from stacktrace

Currently only supports python stacktraces
"""
from __future__ import print_function

import abc
import re
import traceback

import six


class ParseException(Exception):
    pass


class Line(object):
    """Track data for each line in stacktrace"""
    def __init__(self, filename, line_number, function_name, code, class_name=None, native_method=False):
        self.trace_filename = filename
        self.line_number = line_number
        self.function_name = function_name
        self.code = code
        self.class_name = class_name  # Java specific
        self.native_method = native_method  # Java specific
        self.git_filename = None

    def traceback_format(self):
        return (self.trace_filename, self.line_number, self.function_name, self.code)


@six.add_metaclass(abc.ABCMeta)
class Traceback(object):

    def __init__(self, blob):
        self.header = ""
        self.footer = ""
        self.lines = None
        self.extract_traceback(self.prep_blob(blob))

    def prep_blob(self, blob):
        """Cleanup input."""
        # remove empty lines
        if type(blob) == list:
            blob = [line for line in blob if line.strip() != '']
            if len(blob) == 1:
                blob = blob[0].replace('\\n', '\n').split('\n')
        # Split by line
        if type(blob) == str or type(blob) == six.text_type:
            lines = blob.split('\n')
        elif type(blob) == list:
            if len(blob) == 1:
                lines = blob[0].split('\n')
            else:
                lines = [line.rstrip() for line in blob]
        else:
            print(blob)
            raise ParseException("Unknown input format")
        return lines

    @abc.abstractmethod
    def extract_traceback(self, lines):
        """Extract language specific traceback"""
        return

    @abc.abstractmethod
    def format_lines(self):
        """format extracted traceback in same way as traceback."""
        return

    def __str__(self):
        return self.header + self.format_lines() + self.footer

    @abc.abstractmethod
    def file_match(self, trace_filename, git_files):
        """How to match a trace_filename to git_files.

        Generally this varies depending on which is a substring of the other
        """
        return


class PythonTraceback(Traceback):
    """Parse Traceback string."""

    def extract_traceback(self, lines):
        """Convert traceback string into a traceback.extract_tb format"""
        # TODO better logging if cannot read traceback
        # filter out traceback lines
        self.header = lines[0] + '\n'
        if lines[-1] and not lines[-1].startswith(' '):
            self.footer = lines[-1] + '\n'
        lines = [line.rstrip() for line in lines if line.startswith('  ')]
        # extract
        extracted = []
        for i, line in enumerate(lines):
            if i % 2 == 0:
                words = line.split(', ')
                if not (words[0].startswith('  File "') and words[1].startswith('line ') and words[2].startswith('in')):
                    print(line)
                    raise ParseException("Something went wrong parsing stacktrace input.")
                f = words[0].split('"')[1].strip()
                line_number = int(words[1].split(' ')[1])
                function_name = ' '.join(words[2].split(' ')[1:]).strip()
                try:
                    extracted.append(Line(f, line_number, function_name, str(lines[i+1].strip())))
                except IndexError:
                    raise ParseException("Incorrectly extracted traceback information")
        self.lines = extracted
        # Sanity check
        new_lines = traceback.format_list(self.traceback_format())
        new_lines = ('\n'.join([l.rstrip() for l in new_lines]))
        lines = ('\n'.join(lines))
        if lines != new_lines or not self.lines:
            raise ParseException("Incorrectly extracted traceback information")

    def traceback_format(self):
        return [line.traceback_format() for line in self.lines]

    def format_lines(self):
        lines = self.traceback_format()
        return ''.join(traceback.format_list(lines))

    def file_match(self, trace_filename, git_files):
        # trace_filename is substring of git_filename
        return [f for f in git_files if trace_filename.endswith(f)]


class JavaTraceback(Traceback):

    def extract_traceback(self, lines):
        if not lines[0].startswith('\t'):
            self.header = lines[0] + '\n'
        lines = [line for line in lines if line.startswith('\t')]
        extracted = []
        for line in lines:
            extracted.append(self._extract_line(line))
        self.lines = extracted
        if not self.lines:
            raise ParseException("Failed to parse stacktrace")

    def _extract_line(self, line_string):
        if not line_string.startswith('\t'):
            raise ParseException("Missing tab at beginning of line")

        native_method = False
        if line_string.endswith("(Native Method)"):
            # "at java.io.FileInputStream.open(Native Method)"
            native_method = True

        # TODO handle more java traceback formats (unknown source, etc.)
        # TODO get smarter about matching things inside of parens.

        # split on ' ', '(', ')', ':'
        tokens = re.split(" |\(|\)|:", line_string.strip())

        if tokens[0] != "at" or len(tokens) != 5:
            raise ParseException("Invalid Java Exception")

        path = tokens[1].split('.')
        filename = '/'.join(path[:-2] + [tokens[2]])
        function_name = path[-1]
        if not native_method:
            line_number = int(tokens[3])
        else:
            line_number = None
        class_name = path[-2]
        return Line(filename, line_number, function_name, None, class_name, native_method)

    def _format_line(self, line):
        split = line.trace_filename.split('/')
        path = '.'.join(split[:-1])
        filename = split[-1]
        if line.native_method:
            return "\tat %s.%s.%s(Native Method)\n" % (path, line.class_name, line.function_name)
        return "\tat %s.%s.%s(%s:%d)\n" % (path, line.class_name, line.function_name, filename, line.line_number)

    def format_lines(self):
        return ''.join(map(self._format_line, self.lines))

    def file_match(self, trace_filename, git_files):
        # git_filename is substring of trace_filename
        return [f for f in git_files if f.endswith(trace_filename)]


def parse_trace(traceback_string):
    languages = [PythonTraceback, JavaTraceback]
    for language in languages:
        try:
            return language(traceback_string)
        except ParseException:
            # Try next language
            continue
    raise ParseException("Unable to parse traceback")

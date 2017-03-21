"""Extract important filenames, lines, functions and code from stacktrace

Currently only supports python stacktraces
"""
from __future__ import print_function

import abc
import logging
import re
import traceback

import six

log = logging.getLogger(__name__)


class ParseException(Exception):
    pass


class Line(object):
    """Track data for each line in stacktrace"""
    def __init__(self, filename, line_number, function_name, code, class_name=None,
                 native_method=False, unknown_source=False):
        self.trace_filename = filename
        self.line_number = line_number
        self.function_name = function_name
        self.code = code
        self.class_name = class_name  # Java specific
        self.native_method = native_method  # Java specific
        self.unknown_source = unknown_source  # Java specific
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
            message = "Unknown input format"
            log.debug("%s - '%s", message, blob)
            raise ParseException(message)
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

    FILE_LINE_START = '  File "'

    def extract_traceback(self, lines):
        """Convert traceback string into a traceback.extract_tb format"""
        # filter out traceback lines
        self.header = lines[0] + '\n'
        if lines[-1] and not lines[-1].startswith(' '):
            self.footer = lines[-1] + '\n'
        lines = [line.rstrip() for line in lines if line.startswith('  ')]
        # extract
        extracted = []
        code_line = False
        for i, line in enumerate(lines):
            if code_line:
                code_line = False
                continue
            words = line.split(', ')
            if words[0].startswith(self.FILE_LINE_START):
                if not (words[0].startswith('  File "') and words[1].startswith('line ') and words[2].startswith('in')):
                    message = 'Something went wrong parsing stacktrace input.'
                    log.debug("%s - '%s'", message, line)
                    raise ParseException(message)
                f = words[0].split('"')[1].strip()
                line_number = int(words[1].split(' ')[1])
                function_name = ' '.join(words[2].split(' ')[1:]).strip()
                if len(lines) == i + 1 or lines[i + 1].startswith(self.FILE_LINE_START):
                    # Not all lines have code in the traceback
                    code = None
                else:
                    code_line = True
                    code = str(lines[i + 1].strip())

                try:
                    extracted.append(Line(filename=f, line_number=line_number, function_name=function_name, code=code))
                except IndexError:
                    raise ParseException("Incorrectly extracted traceback information")
        self.lines = extracted
        # Sanity check
        new_lines = traceback.format_list(self.traceback_format())
        new_lines = ('\n'.join([l.rstrip() for l in new_lines]))
        lines = ('\n'.join(lines))
        if lines != new_lines or not self.lines:
            message = "Incorrectly extracted traceback information"
            logging.debug("%s: original != parsed\noriginal:\n%s\nparsed:\n%s", message, lines, new_lines)
            raise ParseException(message)

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
        unknown_source = False
        if line_string.endswith("(Native Method)"):
            # "at java.io.FileInputStream.open(Native Method)"
            native_method = True
        if line_string.endswith("(Unknown Source)"):
            # $Lambda$5/1034627183.run(Unknown Source)
            unknown_source = True

        # split on ' ', '(', ')', ':'
        tokens = re.split(r" |\(|\)|:", line_string.strip())

        if tokens[0] != "at" or len(tokens) != 5:
            raise ParseException("Invalid Java Exception")

        path = tokens[1].split('.')
        filename = '/'.join(path[:-2] + [tokens[2]])
        function_name = path[-1]
        if not native_method and not unknown_source:
            line_number = int(tokens[3])
        else:
            line_number = None
        class_name = path[-2]
        return Line(filename, line_number, function_name, None, class_name, native_method, unknown_source)

    def _format_line(self, line):
        split = line.trace_filename.split('/')
        path = '.'.join(split[:-1])
        filename = split[-1]
        if line.native_method:
            return "\tat %s.%s.%s(Native Method)\n" % (path, line.class_name, line.function_name)
        if line.unknown_source:
            return "\tat %s.%s.%s(Unknown Source)\n" % (path, line.class_name, line.function_name)
        return "\tat %s.%s.%s(%s:%d)\n" % (path, line.class_name, line.function_name, filename, line.line_number)

    def format_lines(self):
        return ''.join(map(self._format_line, self.lines))

    def file_match(self, trace_filename, git_files):
        # git_filename is substring of trace_filename
        return [f for f in git_files if f.endswith(trace_filename)]


class ObjectiveCTraceback(Traceback):
    # TODO - Is Objective-C really correct here? Wouldn't this work for Swift
    # as well. Maybe it's more accurate to say this is a "Traceback for iOS
    # crash reports?
    # Crash Report format spec:
    # https://developer.apple.com/library/content/technotes/tn2151/_index.html#//apple_ref/doc/uid/DTS40008184-CH1-ANALYZING_CRASH_REPORTS

    def _parse_to_new_line(self, lines):
        # lines -> (lines until '', remaining lines)
        end_of_header_idx = lines.index('')
        return (lines[:end_of_header_idx], lines[end_of_header_idx:])

    def extract_traceback(self, lines):
        """Extract language specific traceback"""
        self.header = []
        crashed_thread_trace = []
        if "Incident Identifier" in lines[0]:
            # parse apple crash report format
            # parse header
            thread_start_index = lines.index("Thread 0 name:")
            self.header = ''.join(lines[:thread_start_index])
            lines = lines[thread_start_index:]
            # parse the trace of the crashed thread.
            for i, l in enumerate(lines):
                if l.startswith("Thread") and l.strip().endswith('Crashed:'):
                    crashed_thread_idx = i
                    break
            for idx, line in enumerate(lines[crashed_thread_idx + 1:]):
                if line.startswith(str(idx)):
                    crashed_thread_trace.append(line)
                else:
                    break

            print(crashed_thread_trace)
        elif "Crashlytics" in lines[0]:
            pass  # TODO - parse crashlytics
        crashed_thread_trace = [l.strip() for l in crashed_thread_trace]
        extracted = []
        for line in crashed_thread_trace:
            extracted.append(self._extract_line(line))

        self.lines = extracted

        if not crashed_thread_trace:
            raise ParseException("Failed to parse stacktrace")

        return

    def _scan_line_to_char(self, line, character):
        # line -> (scanned line, remaining string)
        character_idx = line.find(character)
        if character_idx == -1:
            return line, ""
        else:
            return line[:character_idx].strip(), line[character_idx:]

    def _extract_line(self, line):
        """
        0   libsystem_kernel.dylib            0x000000018285b014 __pthread_kill + 8
        1   libsystem_pthread.dylib           0x0000000182923450 pthread_kill + 112 (pthread.c:1366)
        """
        # 0, 1, 2, ...
        frame_number, line = self._scan_line_to_char(line, " ")
        # QuartzCore, Pinterest, CoreFoundation, etc.
        module, line = self._scan_line_to_char(line, "0x")
        # Memory Address
        memory_address, line = self._scan_line_to_char(line, " ")
        # Function Call
        file_components_loc = line.rfind("(")

        if file_components_loc == -1:
            function_call, line = line, ""
        else:
            function_call, line = line[:file_components_loc].strip(), line[file_components_loc:]

        # Strip the memory offset information from the function signature
        function_call = function_call.split("+")[0].strip()
        file_components = line.replace("(", "").replace(")", "").split(":")
        if len(file_components) == 2:
            filename, line_number = file_components[0], int(file_components[1])
        else:
            filename, line_number = None, None
        native_method = "Pinterest" not in module
        class_name = self._scan_line_to_char(function_call, " ")[0].replace("[", "").replace("-", "").replace("+", "")
        return Line(filename, line_number, function_call, None,
                    class_name=class_name, native_method=native_method)

    def _format_line(self, line):
        return "\tat %s : (%s:%s)" % (line.function_name, line.trace_filename, line.line_number)

    def format_lines(self):
        return ''.join(map(self._format_line, self.lines))

    def file_match(self, trace_filename, git_files):
        # git_filename is substring of trace_filename
        return [f for f in git_files if f.endswith(trace_filename)]


def parse_trace(traceback_string):
    languages = [PythonTraceback, JavaTraceback, ObjectiveCTraceback]
    for language in languages:
        try:
            return language(traceback_string)
        except ParseException:
            log.debug("Failed to parse as %s", language)
            # Try next language
            continue
    raise ParseException("Unable to parse traceback")

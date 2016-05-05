"""Extract important filenames, lines, functions and code from stacktrace

Currently only supports python stacktraces
"""
import traceback

# TODO turn this into different classes for different languages


class Line(object):
    """Track data for each line in stacktrace"""
    def __init__(self, filename, line_number, function_name, code):
        self.trace_filename = filename
        self.line_number = line_number
        self.function_name = function_name
        self.code = code
        self.git_filename = None

    def traceback_format(self):
        return (self.trace_filename, self.line_number, self.function_name, self.code)


class Traceback(object):
    """Parse Traceback string."""

    def __init__(self, blob, filter_site_packages=False):
        self.lines = None
        self.extract_python_traceback(blob)
        if filter_site_packages:
            self.filter_site_packages()

    def extract_python_traceback(self, blob):
        """Convert traceback string into a traceback.extract_tb format"""
        # remove empty lines
        if type(blob) == list:
            blob = [line for line in blob if line.strip() != '']
            if len(blob) == 1:
                blob = blob[0].replace('\\n', '\n').split('\n')
        # Split by line
        if type(blob) == str or type(blob) == unicode:
            lines = blob.split('\n')
        elif type(blob) == list:
            if len(blob) == 1:
                lines = blob[0].split('\n')
            else:
                lines = [line.rstrip() for line in blob]
        else:
            print blob
            raise Exception("Unknown input format")
        # TODO better logging if cannot read traceback
        # filter out traceback lines
        lines = [line.rstrip() for line in lines if line.startswith('  ')]
        # extract
        extracted = []
        for i, line in enumerate(lines):
            if i % 2 == 0:
                words = line.split(', ')
                if not (words[0].startswith('  File "') and words[1].startswith('line ') and words[2].startswith('in')):
                    print line
                    raise Exception("Something went wrong parsing stacktrace input.")
                f = words[0].split('"')[1].strip()
                line_number = int(words[1].split(' ')[1])
                function_name = ' '.join(words[2].split(' ')[1:]).strip()
                try:
                    extracted.append(Line(f, line_number, function_name, str(lines[i+1].strip())))
                except IndexError:
                    raise Exception("Incorrectly extracted traceback information")
        self.lines = extracted
        # Sanity check
        new_lines = traceback.format_list(self.traceback_format())
        new_lines = ('\n'.join([l.rstrip() for l in new_lines]))
        lines = ('\n'.join(lines))
        if lines != new_lines:
            raise Exception("Incorrectly extracted traceback information")

    def filter_site_packages(self):
        filtered = []
        for line in self.lines:
            if '/site-packages/' not in line.trace_filename:
                filtered.append(line)
        self.lines = filtered

    def traceback_format(self):
        return [line.traceback_format() for line in self.lines]

    def __str__(self):
        lines = self.traceback_format()
        return ''.join(traceback.format_list(lines))

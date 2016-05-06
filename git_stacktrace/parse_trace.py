"""Extract important filenames, lines, functions and code from stacktrace

Currently only supports python stacktraces
"""

import traceback

# TODO turn this into different classes for different languages


def extract_python_traceback(blob):
    """Convert traceback string into a traceback.extract_tb format"""
    # Split by line
    if type(blob) == str:
        lines = blob.split('\n')
    elif type(blob) == list:
        if len(blob) == 1:
            lines = blob[0].split('\n')
        else:
            lines = blob
    else:
        print blob
        raise Exception("Unknown input format")
    # filter out traceback lines
    lines = [line for line in lines if line.startswith('  ')]
    # extract
    extracted = []
    for i, line in enumerate(lines):
        if i % 2 == 0:
            words = line.split(', ')
            if not (words[0].startswith('  File "') and words[1].startswith('line ') and words[2].startswith('in')):
                print line
                raise Exception("Something went wrong parsing stacktrace input.")
            f = words[0].split('"')[1].strip()
            line = int(words[1].split(' ')[1])
            module = ' '.join(words[2].split(' ')[1:]).strip()
            extracted.append((f, line, module, str(lines[i+1].strip())))
    # Sanity check
    new_lines = traceback.format_list(extracted)
    new_lines = ('\n'.join([l.rstrip() for l in new_lines]))
    lines = ('\n'.join(lines))
    if lines != new_lines:
        raise Exception("Incorrectly extracted traceback information")
    return extracted


def extract_python_traceback_from_file(filename):
    with open(filename) as f:
        data = f.read().replace('\\n', '\n')
        return extract_python_traceback(data)


def filter_site_packages(extracted):
    filtered = []
    for f, line, func, code in extracted:
        if '/site-packages/' not in f:
            filtered.append((f, line, func, code))
    return filtered


def print_traceback(extracted):
    print "Traceback:"
    for line in traceback.format_list(extracted):
        print line.rstrip()

from __future__ import print_function

import json
import logging
import os

from cgi import escape
from git_stacktrace import api
from six.moves.BaseHTTPServer import BaseHTTPRequestHandler
from six.moves.BaseHTTPServer import HTTPServer
from six.moves.html_parser import HTMLParser
from six.moves.urllib_parse import parse_qs
from string import Template


def unescape(s):
    return HTMLParser().unescape(s)


class Args(object):
    @staticmethod
    def from_json_body(body):
        return Args(json.loads(body))

    @staticmethod
    def from_path(path):
        return Args(parse_qs(path[2:]))

    def __init__(self, params):
        self.params = params

    def _get_field(self, field, default=''):
        return unescape(self.params.get(field, [default])[0])

    @property
    def type(self):
        return self._get_field('option-type')

    @property
    def range(self):
        return self._get_field('range')

    @property
    def branch(self):
        return self._get_field('branch')

    @property
    def since(self):
        return self._get_field('since')

    @property
    def trace(self):
        return self._get_field('trace')

    @property
    def fast(self):
        return self._get_field('fast') == 'on'

    def validate(self):
        if not self.type:
            return None

        if self.type == 'by-date':
            if not self.since
                return ('Missing `since` value. Plese specify a date.', )
            self.git_range = api.convert_since(self.since, branch=self.branch)
            if not api.valid_range(self.git_range):
                return ("Found no commits in '%s'" % self.git_range, )
        elif self.type == 'by-range':
            self.git_range = self.range
            if not api.valid_range(self.git_range):
                return ("Found no commits in '%s'" % self.git_range, )
        else:
            return ('Invalid options type. Expected `by-date` or `by-range`.', )
        return None

    def get_results(self):
        if self.trace:
            traceback = api.parse_trace(self.trace)
            return api.lookup_stacktrace(traceback, self.git_range, fast=self.fast)
        else:
            return None


class ResultsOutput(object):
    def __init__(self, args):
        self.cwd = os.getcwd()
        self.args = args
        try:
            self.messages = args.validate()
            self.results = args.get_results()
        except Exception as e:
            self.messages = (e.message)
            self.results = None

    def get_json(self):
        if self.results is None:
            return json.dumps({
                'errors': self.messages,
                'commits': [],
            })
        elif len(self.results) == 0:
            return json.dumps({
                'errors': 'No matches found',
                'commits': [],
            })
        else:
            return json.dumps({
                'errors': None,
                'commits': self.results.get_sorted_results_by_dict(),
            })

    def get_html_messages(self):
        if self.messages is None:
            return ''
        with open('git_stacktrace/templates/messages.html') as f:
            t = Template(f.read())
            return t.substitute(
                messages=escape(self.messages)
            ).encode('utf-8')

    def get_html_results(self):
        if not self.results:
            return ''
        else:
            sorted_results = self.results.get_sorted_results()
            return '\n<hr/>\n'.join(
                ['<pre><code>' + escape(str(result)) + '</code></pre>' for result in sorted_results]
            )

    def get_html(self):
        with open('git_stacktrace/templates/page.html') as f:
            t = Template(f.read())
            optionType = 'by-date' if not self.args.type else self.args.type
            return t.substitute(
                pwd=escape(self.cwd),
                messages=self.get_html_messages(),
                range=escape(self.args.range),
                branch=escape(self.args.branch),
                since=escape(self.args.since),
                trace=escape(self.args.trace),
                fast='checked' if self.args.fast else '',
                optionType=escape(optionType),
                isByDate='true' if optionType == 'by-date' else 'false',
                isByRange='true' if optionType == 'by-range' else 'false',
                byDateClass='active' if optionType == 'by-date' else '',
                byRangeClass='active' if optionType == 'by-range' else '',
                results=self.get_html_results()
            ).encode('utf-8')


class GitStacktraceHandler(BaseHTTPRequestHandler):
    def _set_headers(self, code=200, content_type='text/html'):
        self.send_response(code)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def do_HEAD(self):
        self._set_headers()

    def do_GET(self):
        if (self.path == '/' or self.path.startswith('/?')):
            try:
                page = ResultsOutput(Args.from_path(self.path))
                self._set_headers()
                self.wfile.write(page.get_html())
            except Exception as e:
                logging.error(e)
                self._set_headers(500)
        else:
            self._set_headers(404)

    def do_POST(self):
        if (self.path == '/'):
            try:
                page = ResultsOutput(Args.from_json_body(self.rfile.read(34)))
                self._set_headers(200, 'application/json')
                self.wfile.write(page.get_json())
            except Exception as e:
                logging.error(e)
                self._set_headers(500, 'application/json')
                self.wfile.write(json.dumps({'error': e}))
        else:
            self._set_headers(404, 'application/json')


def run(server_class=HTTPServer, handler_class=GitStacktraceHandler, port=80):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd...')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

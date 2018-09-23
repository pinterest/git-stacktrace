from __future__ import print_function

import logging
import os

from cgi import escape
from git_stacktrace import api
from six.moves.BaseHTTPServer import BaseHTTPRequestHandler
from six.moves.BaseHTTPServer import HTTPServer # from http.server import HTTPServer
from six.moves.html_parser import HTMLParser
from six.moves.urllib_parse import parse_qs
from string import Template


def unescape(s):
    return HTMLParser().unescape(s)


class Args(object):
    def __init__(self, path):
        self.params = parse_qs(path[2:])

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
        if self.type == '':
            return ()

        if self.type == 'by-date':
            if self.since == '':
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

    def get_trace(self):
        if self.trace:
            traceback = api.parse_trace(self.trace)
            return api.lookup_stacktrace(traceback, self.git_range, fast=self.fast)
        else:
            return ''


class IndexPage(object):
    def __init__(self, args):
        self.cwd = os.getcwd()
        self.args = args
        try:
            self.messages = args.validate()
            self.output = args.get_trace()
        except Exception as e:
            self.messages = (e.message)
            self.output = ''

    def render_messages(self):
        with open('git_stacktrace/templates/messages.html') as f:
            t = Template(f.read())
            return t.substitute(
                messages=escape(self.messages)
            ).encode('utf-8')

    def render(self):
        with open('git_stacktrace/templates/page.html') as f:
            t = Template(f.read())
            optionType = 'by-date' if self.args.type == '' else self.args.type
            return t.substitute(
                pwd=escape(self.cwd),
                messages=self.render_messages(),
                range=escape(self.args.range),
                branch=escape(self.args.branch),
                since=escape(self.args.since),
                trace=escape(self.args.trace),
                fast='checked' if self.args.fast else '',
                optionType=optionType,
                isByDate='true' if optionType == 'by-date' else 'false',
                isByRange='true' if optionType == 'by-range' else 'false',
                byDateClass='active' if optionType == 'by-date' else '',
                byRangeClass='active' if optionType == 'by-range' else '',
                output=escape(''),
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
                page = IndexPage(Args(self.path))
                self._set_headers()
                self.wfile.write(page.render())
            except Exception as e:
                logging.error(e)
                self._set_headers(500)
        else:
            self._set_headers(404)


def run(server_class=HTTPServer, handler_class=GitStacktraceHandler, port=80):
    print(dir(server_class))
    print(BaseHTTPRequestHandler)

    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd...')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

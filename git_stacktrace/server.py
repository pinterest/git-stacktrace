from __future__ import print_function

import json
import logging
import os

from html import escape
from git_stacktrace import api
from html.parser import HTMLParser
from urllib.parse import parse_qs
from string import Template
from datetime import date, datetime

log = logging.getLogger(__name__)
dir_path = os.path.dirname(os.path.realpath(__file__))


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


class Args(object):
    @staticmethod
    def from_json_body(body):
        return Args(json.loads(body))

    @staticmethod
    def from_qs(query_string):
        return Args(parse_qs(query_string.lstrip("?")))

    def __init__(self, params):
        self.params = params

    def _get_field(self, field, default=""):
        val = self.params.get(field, [default])
        val = val[0] if isinstance(val, list) else val
        return HTMLParser().unescape(val)

    @property
    def type(self):
        return self._get_field("option-type")

    @property
    def range(self):
        return self._get_field("range")

    @property
    def branch(self):
        return self._get_field("branch")

    @property
    def since(self):
        return self._get_field("since")

    @property
    def trace(self):
        return self._get_field("trace")

    @property
    def fast(self):
        return self._get_field("fast") == "on"

    def validate(self):
        if not self.type:
            return None

        if self.type == "by-date":
            if not self.since:
                return "Missing `since` value. Plese specify a date."
            self.git_range = api.convert_since(self.since, branch=self.branch)
            if not api.valid_range(self.git_range):
                return "Found no commits in '%s'" % self.git_range
        elif self.type == "by-range":
            self.git_range = self.range
            if not api.valid_range(self.git_range):
                return "Found no commits in '%s'" % self.git_range
        else:
            return "Invalid `type` value. Expected `by-date` or `by-range`."
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
            self.messages = str(e)
            self.results = None

    def results_as_json(self):
        if self.results is None:
            return json.dumps({"errors": self.messages, "commits": [],}).encode()
        elif len(self.results.results) == 0:
            return json.dumps({"errors": "No matches found", "commits": [],}).encode()
        else:
            return json.dumps(
                {"errors": None, "commits": self.results.get_sorted_results_by_dict(),}, default=json_serial
            ).encode()

    def results_as_html(self):
        if self.results and self.results.results:
            sorted_results = self.results.get_sorted_results()
            return "\n<hr/>\n".join(
                ["<pre><code>" + escape(str(result)) + "</code></pre>" for result in sorted_results]
            )
        else:
            return "\n<hr/>\n<pre><code>No results found.</code></pre>\n"

    def messages_as_html(self):
        if self.messages is None:
            return ""
        with open(os.path.join(dir_path, "templates", "messages.html")) as f:
            return Template(f.read()).substitute(messages=escape(self.messages))

    def render_page(self):
        optionType = "by-date" if not self.args.type else self.args.type
        with open(os.path.join(dir_path, "templates", "page.html")) as f:
            return (
                Template(f.read())
                .substitute(
                    pwd=escape(self.cwd),
                    messages=self.messages_as_html(),
                    range=escape(self.args.range),
                    branch=escape(self.args.branch),
                    since=escape(self.args.since),
                    trace=escape(self.args.trace),
                    fast="checked" if self.args.fast else "",
                    optionType=escape(optionType),
                    isByDate="true" if optionType == "by-date" else "false",
                    isByRange="true" if optionType == "by-range" else "false",
                    byDateClass="active" if optionType == "by-date" else "",
                    byRangeClass="active" if optionType == "by-range" else "",
                    results=self.results_as_html(),
                )
                .encode("utf-8")
            )


class GitStacktraceApplication(object):
    def __init__(self, environ, start_response):
        self.environ = environ
        self.start_response = start_response
        self.path = environ["PATH_INFO"]

    def __iter__(self):
        method = self.environ["REQUEST_METHOD"]
        if method == "GET":
            yield self.do_GET() or b""
        elif method == "POST":
            yield self.do_POST() or b""
        elif method == "HEAD":
            self._set_headers()
            yield b""
        else:
            self._set_headers(500)
            yield b""

    def _set_headers(self, code=200, content_type="text/html"):
        codes = {
            200: "200 OK",
            404: "404 Not Found",
        }
        self.start_response(codes.get(code, "500 Internal Server Error"), [("Content-type", content_type)])

    def _request_body(self):
        content_length = int(self.environ["CONTENT_LENGTH"], 0)
        return self.environ["wsgi.input"].read(content_length)

    def do_GET(self):
        if self.path == "/favicon.ico":
            self._set_headers()
        elif self.path == "/":
            try:
                args = Args.from_qs(self.environ["QUERY_STRING"])
                out = ResultsOutput(args).render_page()
                self._set_headers()
                return out
            except Exception:
                log.exception("Unable to render trace page as html")
                self._set_headers(500)
        else:
            self._set_headers(404)

    def do_POST(self):
        if self.path == "/":
            try:
                args = Args.from_json_body(self._request_body())
                out = ResultsOutput(args).results_as_json()
                self._set_headers(200, "application/json")
                return out
            except Exception as e:
                log.exception("Unable to load trace results as json")
                self._set_headers(500, "application/json")
                return json.dumps({"error": str(e)}).encode()
        else:
            self._set_headers(404, "application/json")


application = GitStacktraceApplication


# Standard library imports
import os
import sys
import time

# PyPI library imports
import toml
import numpy as np

# Local library imports
from dmppl.base import dbg, info, verb, joinP, tmdiff, rdTxt

# Project imports
# NOTE: Roundabout import path for eva_common necessary for unittest.
import dmppl.experiments.eva.eva_common as eva
from dmppl.experiments.eva.eva_html_table import *

# Version-specific imports
version_help = "Python 2.7 or 3.4+ required."
if sys.version_info[0] == 2:
    assert sys.version_info[1] >= 7, version_help
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from urlparse import parse_qs
elif sys.version_info[0] == 3:
    assert sys.version_info[1] >= 4, version_help
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import parse_qs
else:
    assert False, version_help

class EvaHTMLException(Exception): # {{{
    pass
# }}} class EvaHTMLException

def evaLink(f, g, u, x, y, txt, escapeQuotes=False): # {{{
    '''Return the link to a data view.
    '''
    assert f is None or isinstance(f, str), type(f)
    assert g is None or isinstance(g, str), type(g)
    if f is not None:
        assert f in eva.metricNames, f
    if g is not None:
        assert g in eva.metricNames, g
    assert f or g
    assert u is None or isinstance(u, int), type(u)
    assert x is None or isinstance(x, str), type(x)
    assert y is None or isinstance(y, str), type(y)

    assert isinstance(txt, str), type(txt)

    parts_ = []

    if f is not None:
        parts_.append("f=" + str(f))

    if g is not None:
        parts_.append("g=" + str(g))

    if u is not None:
        parts_.append("u=" + str(u))

    if x is not None:
        parts_.append("x=" + str(x))

    if y is not None:
        parts_.append("y=" + str(y))

    ret = (
        '<a href=',
        '&quot;' if escapeQuotes else '"',
        './?',
        '&'.join(parts_),
        '&quot;' if escapeQuotes else '"',
        '>',
        str(txt),
        '</a>',
    )
    return ''.join(ret)
# }}} def evaLink

def evaHtmlString(args, cfg, request): # {{{
    '''Return a string of HTML.

    f     g     -->
    None  None  Default values
    None  Func  1D color, swap f,g
    Func  None  1D color
    Func  Func  2D color

    u     x     y     -->
    None  None  None  Default values
    None  None  Metr  Default u
    None  Metr  None  Default u
    None  Metr  Metr  Table varying u over rows, delta over columns
    Int   None  None  Network graph
    Int   None  Metr  Table varying x over rows, delta over columns
    Int   Metr  None  Table varying y over rows, delta over columns
    Int   Metr  Metr  Ignore u
    '''
    f, g, u, x, y = \
        request['f'], request['g'], request['u'], request['x'], request['y']

    verb("{f,g}(x|y;u) <-- {%s,%s}(%s|%s;%s)" % (f, g, x, y, u))

    # In debug mode (without `python -O`) assertions are caught before an
    # Exception can be raised giving a 404.
    if f is None and g is None:
        # Default values
        f = eva.metricNames[0]

    elif f is None and isinstance(g, str):
        # 1D color
        assert g in eva.metricNames, g

        if g not in eva.metricNames:
            raise EvaHTMLException

        f, g = g, f
    elif isinstance(f, str) and g is None:
        # 1D color
        assert f in eva.metricNames, f

        if f not in eva.metricNames:
            raise EvaHTMLException

    elif isinstance(f, str) and isinstance(g, str):
        # 2D color
        assert f in eva.metricNames, f
        assert g in eva.metricNames, g

        if f not in eva.metricNames:
            raise EvaHTMLException

        if g not in eva.metricNames:
            raise EvaHTMLException

    else:
        assert False


    vcdInfo = toml.load(eva.paths.fname_meainfo)

    if u is None and x is None and y is None:
        # Default values
        tableNotNetwork = True
        u = 0
        x = vcdInfo["unitIntervalVarNames"][0]

    elif u is None and isinstance(x, str) and isinstance(y, str):
        # Table varying u over rows, delta over columns
        tableNotNetwork = True

    elif u is None and (isinstance(x, str) or isinstance(y, str)):
        # Default u
        tableNotNetwork = True
        u = 0

    elif isinstance(u, str) and isinstance(x, str) and isinstance(y, str):
        # Ignore u
        tableNotNetwork = True
        u = None

    elif isinstance(u, str) and x is None and y is None:
        # Network graph
        tableNotNetwork = False

        u = int(u)
        assert 0 <= u, u

        if 0 > u:
            raise EvaHTMLException

    elif isinstance(u, str) and x is None and isinstance(y, str):
        # Table varying x over rows, delta over columns
        tableNotNetwork = True

        u = int(u)
        assert 0 <= u, u

        if 0 > u:
            raise EvaHTMLException

    elif isinstance(u, str) and isinstance(x, str) and y is None:
        # Table varying y over rows, delta over columns
        tableNotNetwork = True

        u = int(u)
        assert 0 <= u, u

        if 0 > u:
            raise EvaHTMLException

    else:
        assert False

    # Every view varies delta - tables by horizontal, networks by edges.
    dsfDeltas = eva.cfgDsfDeltas(cfg) # [(<downsample factor>, <delta>), ...]

    # Sort by delta value, not by downsampling factor.
    dsfDeltas.sort(key=lambda dsf_d: dsf_d[1])

    body_ = []
    if tableNotNetwork:
        xEx, yEx, fnUXY, varCol = \
            calculateTableData(f, g, u, x, y,
                               cfg, dsfDeltas, vcdInfo)

        _exSibRow, exSib = \
            (np.empty((1, 0)),
             np.concatenate((xEx, yEx), axis=1)) if x and y else \
            (xEx, yEx) if x else \
            (yEx, xEx)

        assert _exSibRow.shape[0] == 1, _exSibRow.shape
        exSibRow = [float(v) for v in _exSibRow[0]]

        body_.append(sliderControls())
        body_.append("<table>")

        # Top-most row with title (with nav popovers), and prev/next.
        body_.append(tableTitleRow(f, g, u, x, y,
                                   cfg, dsfDeltas, vcdInfo))

        # Column headers with delta values. Both hi and lo rows.
        body_.append(tableHeaderRows(f, g, u, x, y,
                                     dsfDeltas,
                                     exSibRow))

        body_.append(tableDataRows(f, g, u, x, y,
                                   vcdInfo,
                                   exSib, varCol, fnUXY))

        body_.append("</table>")
    else:
        body_.append("TODO: networkNotTable") # TODO: Holder for SVG

    # Avoid inline JS or CSS for browser caching, but use for standalone files.
    inlineHead = (args.httpd_port == 0)

    return htmlTopFmt(body_, inlineHead, inlineHead)
# }}} def evaHtmlString

class EvaHTTPServer(HTTPServer): # {{{
    def serve_forever(self, args, cfg):
        self.RequestHandlerClass.args = args
        self.RequestHandlerClass.cfg = cfg
        HTTPServer.serve_forever(self)
# }}} class EvaHTTPServer

class EvaHTTPRequestHandler(BaseHTTPRequestHandler): # {{{

    # These are initialized by EvaHTTPServer.serve_forever()
    args, cfg = None, None

    def parseGetRequest(self, path): # {{{
        '''Parse and sanitize GET path.
        '''
        parsed = parse_qs(path.strip("/?")) # Parse query string.
        ret = {k: (parsed[k][0] if k in parsed.keys() else None) \
               for k in ('f', 'g', 'u', 'x', 'y')}
        return ret
    # }}} def parseGetRequest

    def do_GET(self): # {{{

        # Remove leading / which is usually (always?) present.
        self.path = self.path.lstrip('/')

        # Send response.
        if len(self.path) and not self.path.startswith("?") and \
            (self.path.endswith(".css") or self.path.endswith(".js")):

            # Strip off any relative paths to only find CSS and JS files.
            fname = joinP(eva.appPaths.share, os.path.basename(self.path))

            try:
                response = rdTxt(fname)

                self.send_response(200)

                if fname.endswith(".js"):
                    self.send_header("Content-Type",
                                     "application/javascript; charset=utf-8")
                elif fname.endswith(".css"):
                    self.send_header("Content-Type",
                                     "text/css; charset=utf-8")

                responseBytes = response.encode("utf-8")

            except:
                self.send_error(404, "Invalid JS or CSS GET request!")
                return

        elif len(self.path) and self.path.endswith("favicon.ico"):
            # Bug in Chrome requests favicon.ico with every request until it
            # gets 404'd.
            # https://bugs.chromium.org/p/chromium/issues/detail?id=39402
            try:
                faviconFpath = joinP(eva.appPaths.share, "eva_logo.png")
                responseBytes = open(faviconFpath, 'rb').read()

                self.send_response(200)
                self.send_header("Content-Type", "image/x-icon")
            except:
                self.send_error(404, "Cannot read favicon!")

        elif len(self.path) and not self.path.startswith("?"):
            # Unknown requests.
            self.send_response(404)
            return

        else:

            # Generate HTML string and send OK if inputs are valid.
            try:
                response = evaHtmlString(self.args, self.cfg,
                                         self.parseGetRequest(self.path))

                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")

                responseBytes = response.encode("utf-8")

            except EvaHTMLException:
                self.send_error(404, "Invalid GET request!")
                return

        # Send HTTP headers.
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers
        self.send_header("Content-Length", "%d" % len(responseBytes))
        self.end_headers()

        # Send HTML.
        self.wfile.write(responseBytes)

        return
    # }}} def do_GET

# }}} class EvaHTTPRequestHandler

def runHttpDaemon(args, cfg): # {{{
    '''Run local HTTP/HTML daemon serving data visualization pages on request.
    '''

    verb("Starting HTTPD on TCP port %d..." % args.httpd_port, end='')

    httpd = EvaHTTPServer(('', args.httpd_port), EvaHTTPRequestHandler)

    verb("Running...")

    try:
        tm_start = time.time()
        httpd.serve_forever(args, cfg)
    except KeyboardInterrupt:
        tm_stop = time.time()
        verb("Stopped HTTPD server [%s]" % \
            tmdiff(tm_stop - tm_start))

    return
# }}} def runHttpDaemon

def evaHttpd(args): # {{{
    '''Read in result directory like ./foo.eva/ and serve HTML visualizations.
    '''
    assert eva.initPathsDone

    try:
        cfg = eva.loadCfg()

        if 0 != args.httpd_port:
            runHttpDaemon(args, cfg)
        else:
            request = {'f': args.f,
                       'g': args.g,
                       'u': args.u,
                       'x': args.x,
                       'y': args.y}
            print(evaHtmlString(args, cfg, request))
    except IOError as e:
        msg = "IOError: %s: %s\n" % (e.strerror, e.filename)
        sys.stderr.write(msg)

    return 0
# }}} def evaHttpd

if __name__ == "__main__":
    assert False, "Not a standalone script."
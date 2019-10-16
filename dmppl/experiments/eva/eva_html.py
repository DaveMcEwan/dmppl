
# Standard library imports
from itertools import chain
import os
import sys
import time

# PyPI library imports

# Local library imports
from dmppl.base import dbg, info, verb, joinP, tmdiff, rdTxt

# Project imports
# NOTE: Roundabout import path for eva_common necessary for unittest.
import dmppl.experiments.eva.eva_common as eva

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

def sliderControls(): # {{{
    ret = '''\
<div class="controls">
    <input id="thr_max_slider" type="range"
           min="0.0" max="1.0"
           step="0.01" value="1.0"/>
    <p><span id="thr_min_val"></span>
       &le; Pr <span id="thr_andxor"></span> Pr &le;
       <span id="thr_max_val"></span></p>
    <input id="thr_min_slider" type="range"
           min="0.0" max="1.0"
           step="0.01" value="0.0"/>
</div>
'''
    return ret
# }}} def sliderControls

def popoverUl(ulTitle, items): # {{{
    '''Return a string for use in bootstrap popover.
    '''

    assert isinstance(ulTitle, str) and len(ulTitle), ulTitle
    for liName, liHref in items:
        assert isinstance(liName, str) and len(liName), liName
        assert isinstance(liHref, str) and len(liHref), liHref

    liFmt = '<li> <a href=&quot;{liHref}&quot;> {liName} </a> </li>'
    lis = (liFmt.format(liName=liName, liHref=liHref)for liName,liHref in items)

    fmt = '''\
<a tabindex="0"
   role="button"
   href="#"
   title="{ulTitle}"
   data-html="true"
   data-toggle="popover"
   data-trigger="click"
   data-content="<ul>{lis}</ul>">
{ulTitle}
</a>
'''
    return fmt.format(ulTitle=ulTitle, lis=''.join(lis))
# }}} def popoverUl

def htmlHead(inlineJs=True, inlineCss=True): # {{{
    '''Return a string with HTML headers for JS and CSS.
    '''

    fnamesJs = (joinP(eva.appPaths.share, fname) for fname in \
                ("jquery-3.3.1.slim.min.js",
                 "bootstrap-3.3.7.min.js",
                 "eva.js"))

    fnamesCss = (joinP(eva.appPaths.share, fname) for fname in \
                ("bootstrap-3.3.7.min.css",
                 "eva.css"))

    jsTxts = (('<script> %s </script>' % rdTxt(fname)) \
              if inlineJs else \
              ('<script type="text/javascript" src="%s"></script>' % fname)
              for fname in fnamesJs)

    cssTxts = (('<style> %s </style>' % rdTxt(fname)) \
              if inlineCss else \
              ('<link rel="stylesheet" type="text/css" href="%s">' % fname)
              for fname in fnamesCss)

    return "<head>" + '\n'.join(chain(jsTxts, cssTxts)) + "</head>"
# }}} def htmlHead

def evaHtmlString(args, cfg, evcx, request): # {{{
    '''Return a string of HTML.

    f     g     -->
    None  None  invalid
    None  Func  1D color, swap f,g
    Func  None  1D color
    Func  Func  2D color

    u     x     y     -->
    None  None  None  invalid
    None  None  Metr  invalid
    None  Metr  None  invalid
    None  Metr  Metr  Table varying u over rows, delta over columns
    Int   None  None  Network graph
    Int   None  Metr  Table varying x over rows, delta over columns
    Int   Metr  None  Table varying y over rows, delta over columns
    Int   Metr  Metr  Table row varying delta over columns
    '''
    f, g, u, x, y = \
        request['f'], request['g'], request['u'], request['x'], request['y']

    verb("{f,g}(x|y;u) <-- {%s,%s}(%s|%s;%s)" % (f, g, x, y, u))

    if f is None and isinstance(g, str):
        pass # 1D color
        f, g = g, f
    elif isinstance(f, str) and g is None:
        pass # 1D color
    elif isinstance(f, str) and isinstance(g, str):
        pass # 2D color
    else:
        assert False, "At least one of f,g must be string of function name." \
                      " (f%s=%s, g%s=%s)" % (type(f), f, type(g), g)

    if u is None and isinstance(x, str) and isinstance(y, str):
        pass # Table varying u over rows, delta over columns
    elif isinstance(u, str) and x is None and y is None:
        pass # Network graph
    elif isinstance(u, str) and x is None and isinstance(y, str):
        pass # Table varying x over rows, delta over columns
    elif isinstance(u, str) and isinstance(x, str) and y is None:
        pass # Table varying y over rows, delta over columns
    elif isinstance(u, str) and isinstance(x, str) and isinstance(y, str):
        pass # Table row varying delta over columns
    else:
        assert False, "Invalid combination of u,x,y." \
                      " (u=%s, x=%s, y=%s)" % (u, x, y)

    # Avoid inline JS or CSS for browser caching, but use for standalone files.
    inlineHead = (args.httpd_port == 0)
    head = htmlHead(inlineHead, inlineHead)

    u = int(u)
    assert 0 <= u, u

    return head + "TODO"
# }}} def evaHtmlString

class EvaHTMLException(Exception): # {{{
    pass
# }}} class EvaHTMLException

class EvaHTTPServer(HTTPServer): # {{{
    def serve_forever(self, args, cfg, evcx):
        self.RequestHandlerClass.args = args
        self.RequestHandlerClass.cfg = cfg
        self.RequestHandlerClass.evcx = evcx
        HTTPServer.serve_forever(self)
# }}} class EvaHTTPServer

class EvaHTTPRequestHandler(BaseHTTPRequestHandler): # {{{

    # These are initialized by EvaHTTPServer.serve_forever()
    args, cfg, evcx = None, None, None

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
                response = evaHtmlString(self.args, self.cfg, self.evcx,
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

def runHttpDaemon(args, cfg, evcx): # {{{
    '''Run local HTTP/HTML daemon serving data visualization pages on request.
    '''

    verb("Starting HTTPD on TCP port %d..." % args.httpd_port, end='')

    httpd = EvaHTTPServer(('', args.httpd_port), EvaHTTPRequestHandler)

    verb("Running...")

    try:
        tm_start = time.time()
        httpd.serve_forever(args, cfg, evcx)
    except KeyboardInterrupt:
        tm_stop = time.time()
        verb("Stopped HTTPD server [%s]" % \
            tmdiff(tm_stop - tm_start))

    return
# }}} def runHttpDaemon

def evaHtml(args): # {{{
    '''Read in result directory like ./foo.eva/ and serve HTML visualizations.
    '''
    assert eva.initPathsDone

    try:
        cfg = eva.loadCfg()
        evcx = eva.loadEvcx()

        if 0 != args.httpd_port:
            runHttpDaemon(args, cfg, evcx)
        else:
            request = {'f': args.f,
                       'g': args.g,
                       'u': args.u,
                       'x': args.x,
                       'y': args.y}
            print(evaHtmlString(args, cfg, evcx, request))
    except IOError as e:
        msg = "IOError: %s: %s\n" % (e.strerror, e.filename)
        sys.stderr.write(msg)

    return 0
# }}} def evaHtml

if __name__ == "__main__":
    assert False, "Not a standalone script."

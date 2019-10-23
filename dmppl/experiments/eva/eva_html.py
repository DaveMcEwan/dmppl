
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

def htmlTopFmt(inlineJs=True, inlineCss=True): # {{{
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

    ret = (
        '<!DOCTYPE html>',
        '<html>',
        '  <head>',
        '\n'.join(chain(jsTxts, cssTxts)),
        '  </head>',
        '  <body>',
        '    {}',
        '  </body>',
        '</html>',
    )
    return ''.join(r.strip() for r in ret)
# }}} def htmlTopFmt

def evaLink(f, g, u, x, y, txt): # {{{
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
        '<a href="./?',
        '&'.join(parts_),
        '">',
        str(txt),
        '</a>',
    )
    return ''.join(ret)
# }}} def evaLink

def fnDisplay(f, g): # {{{
    assert f is None or isinstance(f, str), type(f)
    assert g is None or isinstance(g, str), type(g)
    if f is not None:
        assert f in eva.metricNames, f
    if g is not None:
        assert g in eva.metricNames, g
    assert f or g, (f, g)
    return ("{%s,%s}" % (f, g)) if f and g else (f if f else g)
# }}} def fnDisplay

def uDisplay(u): # {{{
    assert u is None or isinstance(u, int), type(u)
    return "..." if u is None else str(u)
# }}} def uDisplay

def xDisplay(x): # {{{
    assert x is None or isinstance(x, str), type(x)
    return "..." if x is None else x
# }}} def xDisplay

def yDisplay(y): # {{{
    assert y is None or isinstance(y, str), type(y)
    return "..." if y is None else y
# }}} def yDisplay

evaTitleFmt = "{fn}(x={x} | y={y}<sub>&lang;&delta;&rang;</sub> ; u={u})"

def evaTitleText(f, g, u, x, y): # {{{
    '''Return the title of a data view as a simple string without nested markup.
    '''
    # NOTE: Assertions handled in *Display().
    return evaTitleFmt.format(fn=fnDisplay(f, g),
                              x=xDisplay(x),
                              y=yDisplay(y),
                              u=uDisplay(u))
# }}} def evaTitleText

def evaTitleAny(fn, u, x, y): # {{{
    '''Return the title of a data view substituing in arbitary markup strings.
    '''
    assert isinstance(fn, str), type(fn)
    assert isinstance(u, str), type(u)
    assert isinstance(x, str), type(x)
    assert isinstance(y, str), type(y)
    assert 0 < len(fn), fn
    assert 0 < len(u), u
    assert 0 < len(x), x
    assert 0 < len(y), y

    return evaTitleFmtformat(fn=fn, x=x, y=y, u=u)
# }}} def evaTitleAny

def tableTitleRow(f, g, u, x, y, measureNames, nDeltas, winStride): # {{{
    '''Return a string with HTML tr.
    '''
    #'    <tr>'
    #'        <th class="tabletitle" colspan="{max_colspan}">'
    #'           {title_f}(X={title_x} | Y={title_y}<sub>&lang;&delta;&rang;</sub> ; u=...)'
    #'        </th>'
    #'    </tr>'

    #'    <tr>'
    #'        <th class="tabletitle" colspan="{max_colspan}">'
    #'           {title_f}(X={title_x} | Y=...<sub>&lang;&delta;&rang;</sub> ; u={time_u})'
    #'        </th>'
    #'        <th class="nav_u" colspan="5">{prev_u} {next_u}</th>'
    #'    </tr>'

    #'    <tr>'
    #'        <th class="tabletitle" colspan="{max_colspan}">'
    #'           {title_f}(X=... | Y={title_y}<sub>&lang;&delta;&rang;</sub> ; u={time_u})'
    #'        </th>'
    #'        <th class="nav_u" colspan="5">{prev_u} {next_u}</th>'
    #'    </tr>'

    #title_fmt = ('<a tabindex="0"'
    #             '   role="button"'
    #             '   href="#"'
    #             '   title="{nm}"'
    #             '   data-html="true"'
    #             '   data-toggle="popover"'
    #             '   data-trigger="click"'
    #             '   data-content="<ul>{others}</ul>">'
    #             '{nm}'
    #             '</a>')
    #html_kwargs["title_f"] = title_fmt.format(nm=F, others=''.join(otherFs))
    #html_kwargs["title_x"] = title_fmt.format(nm=offset_name_x, others=''.join(otherXs))
    #html_kwargs["time_u"] = title_fmt.format(nm=time_u, others=''.join(otherUs))

    # NOTE: u may be 0 --> Cannot use "if u".
    if u is None:
        # Possibly overestimate colspanTitle but browsers handle it properly.
        # No need for prev/next navigation since u varies over rows.
        colspanTitle = 8 + nDeltas

        navPrevNext = ''
    else:
        assert isinstance(int, u), type(u)
        # Exactly choose colspan of whole table, then take off some to make
        # room for prev/next navigation links.
        colspanTitle = 7 + nDeltas - 7

        navPrevNext = ' '.join((
            '<th class="nav_u" colspan="5">',
            evaLink(f, g, u - winStride, x, y, "prev"),
            evaLink(f, g, u + winStride, x, y, "next"),
            '</th>',
        ))


    # NOTE: f and g must be valid strings containing name of measurement.
    if f and g:
        fnOthers = [(evaTitleText(fOther, gOther, u, x, y),
                     evaLink(fOther, gOther, u, x, y)) \
                    for fOther in eva.metricNames \
                    for gOther in eva.metricNames \
                    if fOther != f and gOther != g]
    elif f:
        fnOthers = [(evaTitleText(nm, None, u, x, y),
                     evaLink(nm, None, u, x, y)) \
                    for nm in eva.metricNames \
                    if nm != f]
    elif g:
        fnOthers = [(evaTitleText(None, nm, u, x, y),
                     evaLink(None, nm, u, x, y)) \
                    for nm in eva.metricNames \
                    if nm != g]
    else:
        assert False # Checking already performed in evaHtmlString()
    fnPopover = popoverUl(fnDisplay(f, g), fnOthers)

    xOthers = [(evaTitleText(f, g, u, nm, None),
                 evaLink(f, g, u, nm, None)) \
                for nm in measureNames \
                if nm != x]
    xPopover = popoverUl(xDisplay(x), xOthers)

    yOthers = [(evaTitleText(f, g, u, None, nm),
                 evaLink(f, g, u, None, nm)) \
                for nm in measureNames \
                if nm != y]
    yPopover = popoverUl(yDisplay(y), yOthers)


    ret = (
        '<tr>',
        '  <th class="tabletitle" colspan="%d">' % colspanTitle,
        evaTitleAny(fnPopover, xPopover, yPopover, uDisplay(u)),
        '  </th>',
        navPrevNext,
        '</tr>',
    )
    return ''.join(r.strip() for r in ret)
# }}} def tableTitleRow

def evaHtmlString(args, cfg, evcx, request): # {{{
    '''Return a string of HTML.

    f     g     -->
    None  None  invalid
    None  Func  1D color, swap f,g
    Func  None  1D color
    Func  Func  2D color

    u     x     y     -->
    None  None  None  Default values
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
        # 1D color
        assert g in eva.metricNames, g
        f, g = g, f
    elif isinstance(f, str) and g is None:
        # 1D color
        assert f in eva.metricNames, f
    elif isinstance(f, str) and isinstance(g, str):
        # 2D color
        assert f in eva.metricNames, f
        assert g in eva.metricNames, g
    else:
        assert False, "At least one of f,g must be string of function name." \
                      " (f%s=%s, g%s=%s)" % (type(f), f, type(g), g)

    # Every view varies delta - tables by horizontal, networks by edges.
    dsfDeltas = eva.cfgDsfDeltas(cfg) # [(<downsample factor>, <delta>), ...]
    nDeltas = len(dsfDeltas)

    if u is None and isinstance(x, str) and isinstance(y, str):
        # Table varying u over rows, delta over columns
        tableNotNetwork = True

    elif isinstance(u, str) and x is None and y is None:
        # Network graph
        tableNotNetwork = False

        u = int(u)
        assert 0 <= u, u

    elif isinstance(u, str) and x is None and isinstance(y, str):
        # Table varying x over rows, delta over columns
        tableNotNetwork = True

        u = int(u)
        assert 0 <= u, u

    elif isinstance(u, str) and isinstance(x, str) and y is None:
        # Table varying y over rows, delta over columns
        tableNotNetwork = True

        u = int(u)
        assert 0 <= u, u

    elif isinstance(u, str) and isinstance(x, str) and isinstance(y, str):
        # Table row varying delta over columns
        tableNotNetwork = True

        u = int(u)
        assert 0 <= u, u

    else:
        assert False, "Invalid combination of u,x,y." \
                      " (u=%s, x=%s, y=%s)" % (u, x, y)


    body_ = []
    if tableNotNetwork:
        body_.append(sliderControls())
        body_.append("<table>")

        # Top-most row with title (with nav links), and prev/next.
        body_.append(tableTitleRow(f, g, u, x, y,
                                   measureNames, nDeltas, winStride))

        # TODO: Column headers with delta values. Both hi and lo rows.

        # TODO: Data rows.
        body_.append("</table>")
    else:
        body_.append("TODO") # TODO: Holder for SVG

    # Avoid inline JS or CSS for browser caching, but use for standalone files.
    inlineHead = (args.httpd_port == 0)

    return htmlTopFmt(inlineHead, inlineHead).format(''.join(body_))
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

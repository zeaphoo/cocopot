# -*- coding: utf-8 -*-
from functools import update_wrapper
from datetime import datetime, timedelta, date
import time

from .http import HTTP_STATUS_CODES, http_date, html_escape, parse_date
from .utils import json
from ._compat import PY2, to_bytes, string_types, text_type, \
     integer_types, to_unicode, to_native, BytesIO, to_bytes
from .datastructures import HeaderProperty, HeaderDict
from .exceptions import HTTPException, RequestRedirect
if PY2:
    from Cookie import SimpleCookie
else:
    from http.cookies import SimpleCookie


def make_response(*args):
    rv, status_or_headers, headers = args + (None,) * (3 - len(args))

    if rv is None:
        raise ValueError('View function did not return a response')

    if isinstance(status_or_headers, (dict, list)):
        headers, status_or_headers = status_or_headers, None

    if isinstance(rv, (text_type, bytes, bytearray)):
        rv = Response(rv, headers=headers,
                                 status=status_or_headers)
    elif isinstance(rv, HTTPException):
        rv = Response(to_bytes(rv.get_body()), headers=rv.get_headers(),
                                 status=rv.code)
    else:
        if not isinstance(rv, Response):
            raise ValueError('View function returns must be Response or text, not %s'%(rv))

        if status_or_headers is not None:
            if isinstance(status_or_headers, string_types):
                rv.status = status_or_headers
            else:
                rv._status_code = status_or_headers

        if headers:
            headers = headers.items() if isinstance(headers, dict) else headers
            for name, value in headers:
                rv.add_header(name, value)

    return rv

def redirect(location, code=302):
    """Returns a response object (a WSGI application) that, if called,
    redirects the client to the target location.  Supported codes are 301,
    302, 303, 305, and 307.
    Args:
        location: the location the response should redirect to.
        code: the redirect status code. defaults to 302.
    """
    rv = RequestRedirect(location)
    rv.code = code
    return make_response(rv)

def jsonify(*args, **kwargs):
    """Creates a `Response` with the JSON representation of
    the given arguments with an`application/json` mimetype.  The
    arguments to this function are the same as to the `dict`
    constructor.
    Example usage::
        from cocopot import jsonify
        @app.route('/_get_current_user')
        def get_current_user():
            return jsonify(username=g.user.username,
                           email=g.user.email,
                           id=g.user.id)
    This will send a JSON response like this to the browser::
        {
            "username": "admin",
            "email": "admin@localhost",
            "id": 42
        }
    """

    indent = None
    separators = (',', ':')
    rv = Response(json.dumps(dict(*args, **kwargs), indent=indent, separators=separators),
        content_type='application/json')
    return rv

class Response(object):
    """ Storage class for a response body as well as headers and cookies.
        This class does support dict-like case-insensitive item-access to
        headers, but is NOT a dict. Most notably, iterating over a response
        yields parts of the body and not the headers.

        Args:
            body: The response body as one of the supported types.
            status: Either an HTTP status code (e.g. 200) or a status line
                       including the reason phrase (e.g. '200 OK').
            headers: A dictionary or a list of name-value pairs.
        Additional keyword arguments are added to the list of headers.
        Underscores in the header name are replaced with dashes.
    """

    default_status = 200
    default_content_type = 'text/plain; charset=UTF-8'

    # Header blacklist for specific response codes
    # (rfc2616 section 10.2.3 and 10.3.5)
    bad_headers = {
        204: set(('Content-Type', )),
        304: set(('Allow', 'Content-Encoding', 'Content-Language',
                  'Content-Length', 'Content-Range', 'Content-Type',
                  'Content-Md5', 'Last-Modified'))
    }

    def __init__(self, body='', status=None, headers=None, **more_headers):
        self._cookies = None
        self._headers = HeaderDict()
        self.status = status or self.default_status
        self.body = body
        if headers:
            if isinstance(headers, dict):
                headers = headers.items()
            for name, value in headers:
                self.add_header(name, value)
        if more_headers:
            for name, value in more_headers.items():
                self.add_header(name, value)

    def init_with(self, rv, status):
        ret = rv
        self.status = status
        return ret

    def copy(self, cls=None):
        """ Returns a copy of self. """
        cls = cls or Response
        assert issubclass(cls,Response)
        copy = cls()
        copy.status = self.status
        copy._headers = HeaderDict(self._headers.allitems())
        if self._cookies:
            copy._cookies = SimpleCookie()
            copy._cookies.load(self._cookies.output(header=''))
        copy.body = self.body
        return copy

    def __iter__(self):
        return iter(self.body)

    def close(self):
        if hasattr(self.body, 'close'):
            self.body.close()

    @property
    def status_line(self):
        """ The HTTP status line as a string (e.g. ``404 Not Found``)."""
        return self._status_line

    @property
    def status_code(self):
        """ The HTTP status code as an integer (e.g. 404)."""
        return self._status_code

    def _set_status(self, status):
        if isinstance(status, int):
            code, status = status, '%s %s'%(status, HTTP_STATUS_CODES.get(status, 'Unknown'))
        elif ' ' in status:
            status = status.strip()
            code = int(status.split()[0])
        else:
            raise ValueError('String status line without a reason phrase.')
        if not 100 <= code <= 999:
            raise ValueError('Status code out of range.')
        self._status_code = code
        self._status_line = str(status)

    def _get_status(self):
        return self._status_line

    status = property(
        _get_status, _set_status, None,
        ''' A writeable property to change the HTTP response status. It accepts
            either a numeric code (100-999) or a string with a custom reason
            phrase (e.g. "404 Brain not found"). Both `status_line` and
            `status_code` are updated accordingly. The return value is
            always a status string. ''')
    del _get_status, _set_status

    @property
    def headers(self):
        """ An instance of `HeaderDict`, a case-insensitive dict-like
            view on the response headers. """
        return self._headers

    def __contains__(self, name):
        return name in self._headers

    def __delitem__(self, name):
        del self._headers[name]

    def __getitem__(self, name):
        return self._headers[name]

    def __setitem__(self, name, value):
        self._headers[name] = value

    def get_header(self, name, default=None):
        """ Return the value of a previously defined header. If there is no
            header with that name, return a default value. """
        return self._headers.get(name, [default])

    def set_header(self, name, value):
        """ Create a new response header, replacing any previously defined
            headers with the same name. """
        self._headers.replace(name, value)

    def add_header(self, name, value):
        """ Add an additional response header, not removing duplicates. """
        self._headers.append(name, value)

    def iter_headers(self):
        """ Yield (header, value) tuples, skipping headers that are not
            allowed with the current response status code. """
        return self.headerlist

    @property
    def headerlist(self):
        """ WSGI conform list of (header, value) tuples. """
        import cocopot
        out = []
        headers = list(self._headers.allitems())
        if 'Content-Type' not in self._headers:
            headers.append(('Content-Type', self.default_content_type))
        headers.append(('Server', 'Cocopot %s'%(cocopot.__version__)))
        if self._status_code in self.bad_headers:
            bad_headers = self.bad_headers[self._status_code]
            headers = [h for h in headers if h[0] not in bad_headers]
        out.extend(headers)
        if self._cookies:
            for c in self._cookies.values():
                out.append(('Set-Cookie', c.OutputString()))
        if PY2:
            return [(k, v.encode('utf8') if isinstance(v, text_type) else v)
                    for (k, v) in out]
        else:
            return [(k, v.encode('utf8').decode('latin1')) for (k, v) in out]

    content_type = HeaderProperty('Content-Type')
    content_length = HeaderProperty('Content-Length', reader=int)
    expires = HeaderProperty(
        'Expires',
        reader=lambda x: datetime.utcfromtimestamp(parse_date(x)),
        writer=lambda x: http_date(x))

    @property
    def charset(self, default='UTF-8'):
        """ Return the charset specified in the content-type header (default: utf8). """
        if 'charset=' in self.content_type:
            return self.content_type.split('charset=')[-1].split(';')[0].strip()
        return default

    def set_cookie(self, name, value, secret=None, **options):
        """ Create a new cookie or replace an old one. If the `secret` parameter is
            set, create a `Signed Cookie` (described below).

            Args:
                name: the name of the cookie.
                value: the value of the cookie.
                secret: a signature key required for signed cookies.

            Additionally, this method accepts all RFC 2109 attributes that are
            supported by `cookie.Morsel`, including:
                max_age: maximum age in seconds. (default: None)
                expires: a datetime object or UNIX timestamp. (default: None)
                domain: the domain that is allowed to read the cookie. (default: current domain)
                path: limits the cookie to a given path (default: current path)
                secure: limit the cookie to HTTPS connections (default: off).
                httponly: prevents client-side javascript to read this cookie (default: off).

            If neither `expires` nor `max_age` is set (default), the cookie will
            expire at the end of the browser session (as soon as the browser
            window is closed).
            Signed cookies may store any pickle-able object and are
            cryptographically signed to prevent manipulation. Keep in mind that
            cookies are limited to 4kb in most browsers.
            Warning: Signed cookies are not encrypted (the client can still see
            the content) and not copy-protected (the client can restore an old
            cookie). The main intention is to make pickling and unpickling
            save, not to store secret information at client side.
        """
        if not self._cookies:
            self._cookies = SimpleCookie()

        if secret:
            pass
            #value = to_unicode(cookie_encode((name, value), secret))
        elif not isinstance(value, string_types):
            raise TypeError('Secret key missing for non-string Cookie.')

        if len(value) > 4096: raise ValueError('Cookie value to long.')
        self._cookies[name] = value

        for key, value in options.items():
            if key == 'max_age':
                if isinstance(value, timedelta):
                    value = value.seconds + value.days * 24 * 3600
            if key == 'expires':
                if isinstance(value, (date, datetime)):
                    value = value.timetuple()
                elif isinstance(value, (int, float)):
                    value = time.gmtime(value)
                value = time.strftime("%a, %d %b %Y %H:%M:%S GMT", value)
            if key in ('secure', 'httponly') and not value:
                continue
            self._cookies[name][key.replace('_', '-')] = value

    def delete_cookie(self, key, **kwargs):
        """ Delete a cookie. Be sure to use the same `domain` and `path`
            settings as used to create the cookie. """
        kwargs['max_age'] = -1
        kwargs['expires'] = 0
        self.set_cookie(key, '', **kwargs)

    def __repr__(self):
        out = ''
        for name, value in self.headerlist:
            out += '%s: %s\n' % (name.title(), value.strip())
        return out

    def __call__(self, environ, start_response):
        """Process this response as WSGI application.
        """
        start_response(self._status_line, self.headerlist)
        body = self.body if isinstance(self.body, list) else [self.body]
        body = list(map(lambda x: to_bytes(x), body))
        return body

# -*- coding: utf-8 -*-
from functools import update_wrapper
from datetime import datetime, timedelta

from .http import HTTP_STATUS_CODES, http_date
from .utils import cached_property
from ._compat import PY2, to_bytes, string_types, text_type, \
     integer_types, to_unicode, to_native, BytesIO
from .datastructures import HeaderProperty
from .exceptions import HTTPException


class Response(object):
    """ Storage class for a response body as well as headers and cookies.
        This class does support dict-like case-insensitive item-access to
        headers, but is NOT a dict. Most notably, iterating over a response
        yields parts of the body and not the headers.
        :param body: The response body as one of the supported types.
        :param status: Either an HTTP status code (e.g. 200) or a status line
                       including the reason phrase (e.g. '200 OK').
        :param headers: A dictionary or a list of name-value pairs.
        Additional keyword arguments are added to the list of headers.
        Underscores in the header name are replaced with dashes.
    """

    default_status = 200
    default_content_type = 'application/json; charset=UTF-8'

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
        self._headers = {}
        self.body = self.init_with(body, status or self.default_status)
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
        if isinstance(rv, HTTPException):
            status = rv.code
            ret = ''
        self.status = status
        return ret

    def copy(self, cls=None):
        """ Returns a copy of self. """
        cls = cls or Response
        assert issubclass(cls,Response)
        copy = cls()
        copy.status = self.status
        copy._headers = dict((k, v[:]) for (k, v) in self._headers.items())
        if self._cookies:
            copy._cookies = SimpleCookie()
            copy._cookies.load(self._cookies.output(header=''))
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
            code, status = status, '%s %s'%(status, HTTP_STATUS_CODES.get(status))
        elif ' ' in status:
            status = status.strip()
            code = int(status.split()[0])
        else:
            raise ValueError('String status line without a reason phrase.')
        if not 100 <= code <= 999:
            raise ValueError('Status code out of range.')
        self._status_code = code
        self._status_line = str(status or ('%d Unknown' % code))

    def _get_status(self):
        return self._status_line

    status = property(
        _get_status, _set_status, None,
        ''' A writeable property to change the HTTP response status. It accepts
            either a numeric code (100-999) or a string with a custom reason
            phrase (e.g. "404 Brain not found"). Both :data:`status_line` and
            :data:`status_code` are updated accordingly. The return value is
            always a status string. ''')
    del _get_status, _set_status

    @property
    def headers(self):
        """ An instance of :class:`HeaderDict`, a case-insensitive dict-like
            view on the response headers. """
        hdict = HeaderDict()
        hdict.dict = self._headers
        return hdict

    def __contains__(self, name):
        return _hkey(name) in self._headers

    def __delitem__(self, name):
        del self._headers[_hkey(name)]

    def __getitem__(self, name):
        return self._headers[_hkey(name)][-1]

    def __setitem__(self, name, value):
        self._headers[_hkey(name)] = [value if isinstance(value, unicode) else
                                      str(value)]

    def get_header(self, name, default=None):
        """ Return the value of a previously defined header. If there is no
            header with that name, return a default value. """
        return self._headers.get(_hkey(name), [default])[-1]

    def set_header(self, name, value):
        """ Create a new response header, replacing any previously defined
            headers with the same name. """
        self._headers[_hkey(name)] = [value if isinstance(value, unicode)
                                            else str(value)]

    def add_header(self, name, value):
        """ Add an additional response header, not removing duplicates. """
        self._headers.setdefault(_hkey(name), []).append(
            value if isinstance(value, unicode) else str(value))

    def iter_headers(self):
        """ Yield (header, value) tuples, skipping headers that are not
            allowed with the current response status code. """
        return self.headerlist

    @property
    def headerlist(self):
        """ WSGI conform list of (header, value) tuples. """
        out = []
        headers = list(self._headers.items())
        if 'Content-Type' not in self._headers:
            headers.append(('Content-Type', [self.default_content_type]))
        if self._status_code in self.bad_headers:
            bad_headers = self.bad_headers[self._status_code]
            headers = [h for h in headers if h[0] not in bad_headers]
        out += [(name, val) for (name, vals) in headers for val in vals]
        if self._cookies:
            for c in self._cookies.values():
                out.append(('Set-Cookie', c.OutputString()))
        if PY2:
            return [(k, v.encode('utf8') if isinstance(v, unicode) else v)
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
            :param name: the name of the cookie.
            :param value: the value of the cookie.
            :param secret: a signature key required for signed cookies.
            Additionally, this method accepts all RFC 2109 attributes that are
            supported by :class:`cookie.Morsel`, including:
            :param max_age: maximum age in seconds. (default: None)
            :param expires: a datetime object or UNIX timestamp. (default: None)
            :param domain: the domain that is allowed to read the cookie.
              (default: current domain)
            :param path: limits the cookie to a given path (default: current path)
            :param secure: limit the cookie to HTTPS connections (default: off).
            :param httponly: prevents client-side javascript to read this cookie
              (default: off, requires Python 2.6 or newer).
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
            value = to_unicode(cookie_encode((name, value), secret))
        elif not isinstance(value, basestring):
            raise TypeError('Secret key missing for non-string Cookie.')

        if len(value) > 4096: raise ValueError('Cookie value to long.')
        self._cookies[name] = value

        for key, value in options.items():
            if key == 'max_age':
                if isinstance(value, timedelta):
                    value = value.seconds + value.days * 24 * 3600
            if key == 'expires':
                if isinstance(value, (datedate, datetime)):
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
        return self.body

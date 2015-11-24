# -*- coding: utf-8 -*-
from functools import update_wrapper
from datetime import datetime, timedelta
import cgi
from tempfile import TemporaryFile
from .exceptions import HTTPException, BadRequest
from .utils import cached_property
from .datastructures import MultiDict, FileUpload, FormsDict, WSGIHeaders
from ._compat import (PY2, to_bytes, string_types, text_type,
     integer_types, to_unicode, to_native, BytesIO)
if PY2:
    from Cookie import SimpleCookie
else:
    from http.cookies import SimpleCookie
from .utils import (urlencode, urldecode, urlquote, urlunquote, urljoin, json)
from .http import (parse_content_type, parse_date, parse_auth, parse_content_type, parse_range_header)

from .exceptions import BadRequest

MEMFILE_MAX = 4*1024*1024

class Request(object):
    """
    """

    #: the charset for the request, defaults to utf-8
    charset = 'utf-8'

    #: the error handling procedure for errors, defaults to 'replace'
    encoding_errors = 'replace'

    endpoint = ''

    #: a dict of view arguments that matched the request.  If an exception
    #: happened when matching, this will be `None`.
    view_args = None

    def __init__(self, environ, populate_request=True):
        self.environ = environ
        if populate_request:
            self.environ['cocopot.request'] = self

    def __repr__(self):
        # make sure the __repr__ even works if the request was created
        # from an invalid WSGI environment.  If we display the request
        # in a debug session we don't want the repr to blow up.
        args = []
        try:
            args.append("'%s'" % to_native(self.url, self.url_charset))
            args.append('[%s]' % self.method)
        except Exception:
            args.append('(invalid WSGI environ)')

        return '<%s %s>' % (
            self.__class__.__name__,
            ' '.join(args)
        )

    @property
    def url_charset(self):
        """The charset that is assumed for URLs.  Defaults to the value
        of `charset`.

        """
        return self.charset

    def close(self):
        """Closes associated resources of this request object.  This
        closes all file handles explicitly.  You can also use the request
        object in a with statement with will automatically close it.

        """
        if hasattr(self.stream, 'close'):
            self.stream.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    @cached_property
    def stream(self):
        stream = self.get_input_stream()
        stream.seek(0)
        return stream

    @property
    def input_stream(self):
        return self.environ.get('wsgi.input')

    @cached_property
    def args(self):
        query_string = self.environ.get('QUERY_STRING', '')
        if query_string:
            return MultiDict(urldecode(query_string))
        else:
            return MultiDict()

    @property
    def data(self):
        return self.get_data()

    def get_data(self, cache=True, as_text=False):
        """This reads the buffered incoming data from the client into one
        bytestring.  By default this is cached but that behavior can be
        changed by setting `cache` to `False`.

        Usually it's a bad idea to call this method without checking the
        content length first as a client could send dozens of megabytes or more
        to cause memory problems on the server.

        If `as_text` is set to `True` the return value will be a decoded
        unicode string.

        """
        rv = getattr(self, '_cached_data', None)
        if rv is None:
            rv = self.stream.read()
            if cache:
                self._cached_data = rv
        if as_text:
            rv = rv.decode(self.charset, self.encoding_errors)
        return rv

    @cached_property
    def chunked(self):
        """ True if Chunked transfer encoding was. """
        return 'chunked' in self.environ.get('HTTP_TRANSFER_ENCODING', '').lower()

    def iter_body(self, read, bufsize):
        maxread = max(0, self.content_length)
        while maxread:
            part = read(min(maxread, bufsize))
            if not part: break
            yield part
            maxread -= len(part)

    def iter_chunked(self, read, bufsize):
        err = BadRequest('Error while parsing chunked transfer body.')
        rn, sem, bs = to_bytes('\r\n'), to_bytes(';'), to_bytes('')
        while True:
            header = read(1)
            while header[-2:] != rn:
                c = read(1)
                header += c
                if not c: raise err
                if len(header) > bufsize: raise err
            size, _, _ = header.partition(sem)
            try:
                maxread = int(to_native(size.strip()), 16)
            except ValueError:
                raise err
            if maxread == 0: break
            buff = bs
            while maxread > 0:
                if not buff:
                    buff = read(min(maxread, bufsize))
                part, buff = buff[:maxread], buff[maxread:]
                if not part: raise err
                yield part
                maxread -= len(part)
            if read(2) != rn:
                raise err

    def get_input_stream(self):
        try:
            read_func = self.environ['wsgi.input'].read
        except KeyError:
            self.environ['wsgi.input'] = BytesIO()
            return self.environ['wsgi.input']
        if self.chunked:
            body, body_size, is_temp_file = BytesIO(), 0, False
            for part in self.iter_chunked(read_func, MEMFILE_MAX):
                body.write(part)
                body_size += len(part)
                if not is_temp_file and body_size > MEMFILE_MAX:
                    body, tmp = TemporaryFile(mode='w+b'), body
                    body.write(tmp.getvalue())
                    del tmp
                    is_temp_file = True
        else:
            if self.content_length > MEMFILE_MAX:
                body = TemporaryFile(mode='w+b')
            else:
                body = BytesIO()
                for part in self.iter_body(read_func, MEMFILE_MAX):
                    body.write(part)
        self.environ['wsgi.input'] = body
        body.seek(0)
        return body

    def parse_form_data(self):
        post = FormsDict()
        # We default to application/x-www-form-urlencoded for everything that
        # is not multipart and take the fast path (also: 3.1 workaround)
        if not self.content_type.startswith('multipart/'):
            pairs = urldecode(to_unicode(self.get_data()))
            for key, value in pairs:
                post[key] = value
            return post

        safe_env = {'QUERY_STRING': ''}  # Build a safe environment for cgi
        for key in ('REQUEST_METHOD', 'CONTENT_TYPE', 'CONTENT_LENGTH'):
            if key in self.environ:
                safe_env[key] = self.environ[key]
        args = dict(fp=self.stream, environ=safe_env, keep_blank_values=True)
        if not PY2:
            args['encoding'] = 'utf8'
        data = cgi.FieldStorage(**args)
        self.environ['_cgi.FieldStorage'] = data  #http://bugs.python.org/issue18394
        data = data.list or []
        for item in data:
            if item.filename:
                post[item.name] = FileUpload(item.file, item.name,
                                             item.filename, item.headers)
            else:
                post[item.name] = item.value
        return post

    @cached_property
    def parsed_form_data(self):
        return self.parse_form_data()

    @cached_property
    def form(self):
        form = FormsDict()
        for name, item in self.parsed_form_data.allitems():
            if not isinstance(item, FileUpload):
                form[name] = item
        return form

    @cached_property
    def values(self):
        """Combined multi dict for `args` and `form`."""
        args = []
        for d in self.args, self.form:
            if not isinstance(d, MultiDict):
                for k, v in d.items():
                    args.append((k, v))
            else:
                for k, v in d.iterallitems():
                    args.append((k, v))
        return MultiDict(args)

    @cached_property
    def files(self):
        files = FormsDict()
        for name, item in self.parsed_form_data.allitems():
            if isinstance(item, FileUpload):
                files[name] = item
        return files

    def get_host(self):
        """Return the real host for the given WSGI environment.  This first checks
        the `X-Forwarded-Host` header, then the normal `Host` header, and finally
        the `SERVER_NAME` environment variable (using the first one it finds).
        """
        environ = self.environ
        if 'HTTP_X_FORWARDED_HOST' in environ:
            rv = environ['HTTP_X_FORWARDED_HOST'].split(',', 1)[0].strip()
        elif 'HTTP_HOST' in environ:
            rv = environ['HTTP_HOST']
        else:
            rv = environ['SERVER_NAME']
            if (environ['wsgi.url_scheme'], environ['SERVER_PORT']) not \
               in (('https', '443'), ('http', '80')):
                rv += ':%s'%(environ['SERVER_PORT'])
        return rv


    def get_content_length(self):
        """Returns the content length from the WSGI environment as
        integer.  If it's not available `None` is returned.
        """
        content_length = self.environ.get('CONTENT_LENGTH')
        if content_length is not None:
            try:
                return max(0, int(content_length))
            except (ValueError, TypeError):
                pass
        return 0

    def get_current_url(self, root_only=False, strip_querystring=False, host_only=False):
        """A handy helper function that recreates the full URL as IRI for the
        current request or parts of it.  Here an example:

        >>> get_current_url()
        'http://localhost/script/?param=foo'
        >>> get_current_url(root_only=True)
        'http://localhost/script/'
        >>> get_current_url(host_only=True)
        'http://localhost/'
        >>> get_current_url(strip_querystring=True)
        'http://localhost/script/'
        """
        environ = self.environ
        tmp = [environ['wsgi.url_scheme'], '://', self.get_host()]
        cat = tmp.append
        if host_only:
            return ''.join(tmp) + '/'
        cat(urlquote(environ.get('SCRIPT_NAME', '')).rstrip('/'))
        cat('/')
        if not root_only:
            print(type(environ.get('PATH_INFO')))
            cat(urlquote(environ.get('PATH_INFO', '').lstrip('/')))
            if not strip_querystring:
                qs = self.query_string
                if qs:
                    cat('?' + qs)
        return ''.join(tmp)

    @cached_property
    def cookies(self):
        """Read only access to the retrieved cookie values as dictionary."""
        cookies = SimpleCookie(self.environ.get('HTTP_COOKIE', '')).values()
        return FormsDict((c.key, c.value) for c in cookies)

    def get_cookie(self, key):
        """ Return the content of a cookie. """
        value = self.cookies.get(key)
        return value

    @cached_property
    def headers(self):
        """The headers from the WSGI environ as immutable
        `~cocopot.datastructures.WSGIHeaders`.
        """
        return WSGIHeaders(self.environ)

    @cached_property
    def path(self):
        """Requested path as unicode.  This works a bit like the regular path
        info in the WSGI environment but will always include a leading slash,
        even if the URL root is accessed.
        """
        return '/' + to_unicode(self.environ.get('PATH_INFO', '')).lstrip('/')

    @property
    def script_name(self):
        """ The initial portion of the URL's `path` that was removed by a higher
            level (server or routing middleware) before the application was
            called. This script path is returned with leading and tailing
            slashes. """
        script_name = self.environ.get('SCRIPT_NAME', '').strip('/')
        return '/' + script_name + '/' if script_name else '/'

    @property
    def full_path(self):
        """Requested path as unicode, including the query string."""
        return urljoin(self.script_name, self.path.lstrip('/'))

    @cached_property
    def script_root(self):
        """The root path of the script without the trailing slash."""
        raw_path = to_unicode(self.environ.get('SCRIPT_NAME') or '',
                                       self.charset, self.encoding_errors)
        return raw_path.rstrip('/')

    @cached_property
    def url(self):
        """The reconstructed current URL as IRI.
        """
        return self.get_current_url()

    @cached_property
    def base_url(self):
        """Like `url` but without the querystring
        """
        return self.get_current_url(strip_querystring=True)

    @cached_property
    def root_url(self):
        """The full URL root (with hostname), this is the application
        root as IRI.
        """
        return self.get_current_url(root_only=True)

    @cached_property
    def host_url(self):
        """Just the host with scheme as IRI.
        """
        return self.get_current_url(host_only=True)

    @cached_property
    def host(self):
        """Just the host including the port if available.
        """
        return self.get_host()

    @property
    def query_string(self):
        return self.environ.get('QUERY_STRING', '')

    @property
    def method(self):
        return self.environ.get('REQUEST_METHOD', 'GET').upper()

    @cached_property
    def access_route(self):
        """If a forwarded header exists this is a list of all ip addresses
        from the client ip to the last proxy server.
        """
        if 'HTTP_X_FORWARDED_FOR' in self.environ:
            addr = self.environ['HTTP_X_FORWARDED_FOR'].split(',')
            return list([x.strip() for x in addr])
        elif 'REMOTE_ADDR' in self.environ:
            return list([self.environ['REMOTE_ADDR']])
        return list()

    remote_route = access_route

    @property
    def remote_addr(self):
        """The remote address of the client."""
        route = self.access_route
        return route[0] if route else None


    is_xhr = property(lambda x: x.environ.get('HTTP_X_REQUESTED_WITH', '')
                      .lower() == 'xmlhttprequest', doc='''
        True if the request was triggered via a JavaScript XMLHttpRequest.
        This only works with libraries that support the `X-Requested-With`
        header and set it to "XMLHttpRequest".  Libraries that do that are
        prototype, jQuery and Mochikit and probably some more.''')
    is_secure = property(lambda x: x.environ['wsgi.url_scheme'] == 'https',
                         doc='`True` if the request is secure.')


    @cached_property
    def if_modified_since(self):
        """The parsed `If-Modified-Since` header as datetime object."""
        return parse_date(self.environ.get('HTTP_IF_MODIFIED_SINCE'))

    @cached_property
    def if_unmodified_since(self):
        """The parsed `If-Unmodified-Since` header as datetime object."""
        return parse_date(self.environ.get('HTTP_IF_UNMODIFIED_SINCE'))


    @cached_property
    def range(self):
        """The parsed `Range` header.
        """
        return parse_range_header(self.environ.get('HTTP_RANGE'))


    @cached_property
    def authorization(self):
        header = self.environ.get('HTTP_AUTHORIZATION')
        if not header: return None
        return parse_auth(header)

    @property
    def content_type(self):
        return self.environ.get('CONTENT_TYPE', '')


    @cached_property
    def content_length(self):
        """The Content-Length entity-header field indicates the size of the
        entity-body in bytes or, in the case of the HEAD method, the size of
        the entity-body that would have been sent had the request been a
        GET.
        """
        return self.get_content_length()

    @cached_property
    def parsed_content_type(self):
        return parse_content_type(self.environ.get('CONTENT_TYPE', ''))

    @property
    def mimetype(self):
        """Like `content_type` but without parameters (eg, without
        charset, type etc.).  For example if the content
        type is ``text/html; charset=utf-8`` the mimetype would be
        ``'text/html'``.
        """
        return self.parsed_content_type[0]

    @property
    def mimetype_params(self):
        """The mimetype parameters as dict.  For example if the content
        type is ``text/html; charset=utf-8`` the params would be
        ``{'charset': 'utf-8'}``.
        """
        return self.parsed_content_type[1]

    @property
    def blueprint(self):
        """The name of the current blueprint"""
        if '.' in self.endpoint:
            return self.endpoint.rsplit('.', 1)[0]

    @property
    def json(self):
        """If the mimetype is `application/json` this will contain the
        parsed JSON data.  Otherwise this will be `None`.

        The `get_json` method should be used instead.
        """
        return self.get_json(silent=True)

    def get_json(self, force=False, silent=False, cache=True):
        """Parses the incoming JSON request data and returns it.  If
        parsing fails the `on_json_loading_failed` method on the
        request object will be invoked.  By default this function will
        only load the json data if the mimetype is ``application/json``
        but this can be overriden by the `force` parameter.

        Args:
            force: if set to `True` the mimetype is ignored.
            silent: if set to `False` this method will fail silently
                       and return `False`.
            cache: if set to `True` the parsed JSON data is remembered
                      on the request.
        """
        _missing = object()
        rv = getattr(self, '_cached_json', _missing)
        if rv is not _missing:
            return rv

        if self.mimetype != 'application/json' and not force:
            return None

        # We accept a request charset against the specification as
        # certain clients have been using this in the past.  This
        # fits our general approach of being nice in what we accept
        # and strict in what we send out.
        request_charset = self.mimetype_params.get('charset', 'utf-8')
        try:
            data = to_unicode(self.get_data(cache=False))
            if request_charset is not None:
                rv = json.loads(data, encoding=request_charset)
            else:
                rv = json.loads(data)
        except ValueError as e:
            if silent:
                rv = None
            else:
                raise BadRequest()
        if cache:
            self._cached_json = rv
        return rv

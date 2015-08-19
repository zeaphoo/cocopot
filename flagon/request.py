# -*- coding: utf-8 -*-
"""
    flagon.request
"""
from functools import update_wrapper
from datetime import datetime, timedelta

from .utils import cached_property
from .datastructures import MultiDict, iter_multi_items, FileUpload, FormsDict
from ._compat import (PY2, to_bytes, string_types, text_type,
     integer_types, to_unicode, to_native, BytesIO)
if PY2:
    from Cookie import SimpleCookie
else:
    from http.cookies import SimpleCookie
from .wsgi import (get_input_stream, parse_form_data, urlencode, urldecode,
                    urlquote, urlunquote, get_content_length, get_host, get_current_url)
from .http import (parse_content_type, parse_date, parse_auth, parse_content_type, parse_range_header)

from .exceptions import BadRequest

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

    #: if matching the URL failed, this is the exception that will be
    #: raised / was raised as part of the request handling.  This is
    #: usually a :exc:`~flagon.exceptions.NotFound` exception or
    #: something similar.
    routing_exception = None

    def __init__(self, environ, populate_request=True):
        self.environ = environ
        if populate_request:
            self.environ['flagon.request'] = self

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
        of :attr:`charset`.

        """
        return self.charset

    def close(self):
        """Closes associated resources of this request object.  This
        closes all file handles explicitly.  You can also use the request
        object in a with statement with will automatically close it.

        """
        files = self.__dict__.get('files')
        for key, value in iter_multi_items(files or ()):
            value.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    @cached_property
    def stream(self):
        stream = get_input_stream(self.environ)
        stream.seek(0)
        return stream

    @property
    def input_stream(self):
        return self.environ.get('wsgi.input')

    @cached_property
    def args(self):
        return MultiDict(urldecode(self.environ.get('QUERY_STRING', '')))

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
    def parsed_form_data(self):
        return parse_form_data(self.stream, self.environ)

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
                for k, v in d.items():
                    for lv in v:
                        args.append((k, lv))
        return MultiDict(args)

    @cached_property
    def files(self):
        files = FormsDict()
        for name, item in self.parsed_form_data.allitems():
            if isinstance(item, FileUpload):
                files[name] = item
        return files

    @cached_property
    def cookies(self):
        """Read only access to the retrieved cookie values as dictionary."""
        cookies = SimpleCookie(self.environ.get('HTTP_COOKIE', '')).values()
        return FormsDict((c.key, c.value) for c in cookies)

    @cached_property
    def headers(self):
        """The headers from the WSGI environ as immutable
        `~flagon.datastructures.WSGIHeaders`.
        """
        return WSGIHeaders(self.environ)

    @cached_property
    def path(self):
        """Requested path as unicode.  This works a bit like the regular path
        info in the WSGI environment but will always include a leading slash,
        even if the URL root is accessed.
        """
        return '/' + self.environ.get('PATH_INFO', '').lstrip('/')

    @cached_property
    def full_path(self):
        """Requested path as unicode, including the query string."""
        return self.path + u'?' + to_unicode(self.query_string, self.url_charset)

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
        return get_current_url(self.environ)

    @cached_property
    def base_url(self):
        """Like :attr:`url` but without the querystring
        """
        return get_current_url(self.environ, strip_querystring=True)

    @cached_property
    def url_root(self):
        """The full URL root (with hostname), this is the application
        root as IRI.
        """
        return get_current_url(self.environ, root_only=True)

    @cached_property
    def host_url(self):
        """Just the host with scheme as IRI.
        """
        return get_current_url(self.environ, host_only=True)

    @cached_property
    def host(self):
        """Just the host including the port if available.
        """
        return get_host(self.environ)

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

    @property
    def remote_addr(self):
        """The remote address of the client."""
        return self.environ.get('REMOTE_ADDR')


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

        .. versionadded:: 0.7

        :rtype: :class:`~flagon.datastructures.Range`
        """
        return parse_range_header(self.environ.get('HTTP_RANGE'))


    @cached_property
    def authorization(self):
        """The `Authorization` object in parsed form."""
        header = self.environ.get('HTTP_AUTHORIZATION')
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
        return get_content_length(self.environ)

    @cached_property
    def parsed_content_type(self):
        return parse_content_type(self.environ.get('CONTENT_TYPE', ''))

    @property
    def mimetype(self):
        """Like :attr:`content_type` but without parameters (eg, without
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

        The :meth:`get_json` method should be used instead.
        """
        return self.get_json()

    def get_json(self, force=False, silent=False, cache=True):
        """Parses the incoming JSON request data and returns it.  If
        parsing fails the :meth:`on_json_loading_failed` method on the
        request object will be invoked.  By default this function will
        only load the json data if the mimetype is ``application/json``
        but this can be overriden by the `force` parameter.

        :param force: if set to `True` the mimetype is ignored.
        :param silent: if set to `False` this method will fail silently
                       and return `False`.
        :param cache: if set to `True` the parsed JSON data is remembered
                      on the request.
        """
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
            data = self.get_data(self, cache=False)
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

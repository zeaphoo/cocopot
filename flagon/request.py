# -*- coding: utf-8 -*-
"""
    flagon.request
"""
from functools import update_wrapper
from datetime import datetime, timedelta

from .http import HTTP_STATUS_CODES
from .http.urls import url_decode, iri_to_uri, url_join
from .utils import cached_property
from .datastructures import MultiDict
from ._compat import to_bytes, string_types, text_type, \
     integer_types, wsgi_decoding_dance, wsgi_get_bytes, \
     to_unicode, to_native, BytesIO

from .exceptions import BadRequest

from .globals import current_app


class Request(object):
    """
    """

    #: the charset for the request, defaults to utf-8
    charset = 'utf-8'

    #: the error handling procedure for errors, defaults to 'replace'
    encoding_errors = 'replace'

    #: the maximum content length.  This is forwarded to the form data
    #: parsing function (:func:`parse_form_data`).  When set and the
    #: :attr:`form` or :attr:`files` attribute is accessed and the
    #: parsing fails because more than the specified value is transmitted
    #: a :exc:`~flagon.exceptions.RequestEntityTooLarge` exception is raised.
    #:
    #: Have a look at :ref:`dealing-with-request-data` for more details.
    #:
    #: .. versionadded:: 0.5
    max_content_length = None

    #: the maximum form field size.  This is forwarded to the form data
    #: parsing function (:func:`parse_form_data`).  When set and the
    #: :attr:`form` or :attr:`files` attribute is accessed and the
    #: data in memory for post data is longer than the specified value a
    #: :exc:`~flagon.exceptions.RequestEntityTooLarge` exception is raised.
    #:
    #: Have a look at :ref:`dealing-with-request-data` for more details.
    #:
    #: .. versionadded:: 0.5
    max_form_memory_size = None


    #: Optionally a list of hosts that is trusted by this request.  By default
    #: all hosts are trusted which means that whatever the client sends the
    #: host is will be accepted.
    #:
    #: This is the recommended setup as a webserver should manually be set up
    #: to only route correct hosts to the application, and remove the
    #: `X-Forwarded-Host` header if it is not being used (see
    #: :func:`flagon.wsgi.get_host`).
    #:
    #: .. versionadded:: 0.9
    trusted_hosts = None

    #: Indicates whether the data descriptor should be allowed to read and
    #: buffer up the input stream.  By default it's enabled.
    #:
    #: .. versionadded:: 0.9
    disable_data_descriptor = False

    #: the internal URL rule that matched the request.  This can be
    #: useful to inspect which methods are allowed for the URL from
    #: a before/after handler (``request.url_rule.methods``) etc.
    #:
    #: .. versionadded:: 0.6
    url_rule = None

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

        .. versionadded:: 0.6
        """
        return self.charset

    @classmethod
    def application(cls, f):
        """Decorate a function as responder that accepts the request as first
        argument.  This works like the :func:`responder` decorator but the
        function is passed the request object as first argument and the
        request object will be closed automatically::

            @Request.application
            def my_wsgi_app(request):
                return Response('Hello World!')

        :param f: the WSGI callable to decorate
        :return: a new WSGI callable
        """
        #: return a callable that wraps the -2nd argument with the request
        #: and calls the function with all the arguments up to that one and
        #: the request.  The return value is then called with the latest
        #: two arguments.  This makes it possible to use this decorator for
        #: both methods and standalone WSGI functions.
        def application(*args):
            request = cls(args[-2])
            with request:
                return f(*args[:-2] + (request,))(*args[-2:])
        return update_wrapper(application, f)

    def _get_file_stream(self, total_content_length, content_type, filename=None,
                        content_length=None):
        """Called to get a stream for the file upload.

        This must provide a file-like class with `read()`, `readline()`
        and `seek()` methods that is both writeable and readable.

        The default implementation returns a temporary file if the total
        content length is higher than 500KB.  Because many browsers do not
        provide a content length for the files only the total content
        length matters.

        :param total_content_length: the total content length of all the
                                     data in the request combined.  This value
                                     is guaranteed to be there.
        :param content_type: the mimetype of the uploaded file.
        :param filename: the filename of the uploaded file.  May be `None`.
        :param content_length: the length of this file.  This value is usually
                               not provided because webbrowsers do not provide
                               this value.
        """
        return default_stream_factory(total_content_length, content_type,
                                      filename, content_length)

    @property
    def want_form_data_parsed(self):
        """Returns True if the request method carries content.  As of
        Werkzeug 0.9 this will be the case if a content type is transmitted.

        .. versionadded:: 0.8
        """
        return bool(self.environ.get('CONTENT_TYPE'))

    def make_form_data_parser(self):
        """Creates the form data parser.  Instanciates the
        :attr:`form_data_parser_class` with some parameters.

        .. versionadded:: 0.8
        """
        return self.form_data_parser_class(self._get_file_stream,
                                           self.charset,
                                           self.encoding_errors,
                                           self.max_form_memory_size,
                                           self.max_content_length,
                                           self.parameter_storage_class)

    def _load_form_data(self):
        """Method used internally to retrieve submitted data.  After calling
        this sets `form` and `files` on the request object to multi dicts
        filled with the incoming form data.  As a matter of fact the input
        stream will be empty afterwards.  You can also call this method to
        force the parsing of the form data.

        .. versionadded:: 0.8
        """
        # abort early if we have already consumed the stream
        if 'form' in self.__dict__:
            return

        if self.want_form_data_parsed:
            content_type = self.environ.get('CONTENT_TYPE', '')
            content_length = get_content_length(self.environ)
            mimetype, options = parse_options_header(content_type)
            parser = self.make_form_data_parser()
            data = parser.parse(self._get_stream_for_parsing(),
                                mimetype, content_length, options)
        else:
            data = (self.stream, self.parameter_storage_class(),
                    self.parameter_storage_class())

        # inject the values into the instance dict so that we bypass
        # our cached_property non-data descriptor.
        d = self.__dict__
        d['stream'], d['form'], d['files'] = data

    def _get_stream_for_parsing(self):
        """This is the same as accessing :attr:`stream` with the difference
        that if it finds cached data from calling :meth:`get_data` first it
        will create a new stream out of the cached data.

        .. versionadded:: 0.9.3
        """
        cached_data = getattr(self, '_cached_data', None)
        if cached_data is not None:
            return BytesIO(cached_data)
        return self.stream

    def close(self):
        """Closes associated resources of this request object.  This
        closes all file handles explicitly.  You can also use the request
        object in a with statement with will automatically close it.

        .. versionadded:: 0.9
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
        """The stream to read incoming data from.  Unlike :attr:`input_stream`
        this stream is properly guarded that you can't accidentally read past
        the length of the input.  Werkzeug will internally always refer to
        this stream to read data which makes it possible to wrap this
        object with a stream that does filtering.

        .. versionchanged:: 0.9
           This stream is now always available but might be consumed by the
           form parser later on.  Previously the stream was only set if no
           parsing happened.
        """
        return get_input_stream(self.environ)

    input_stream = environ_property('wsgi.input', 'The WSGI input stream.\n'
        'In general it\'s a bad idea to use this one because you can easily '
        'read past the boundary.  Use the :attr:`stream` instead.')

    @cached_property
    def args(self):
        """The parsed URL parameters.  By default an
        :class:`~flagon.datastructures.ImmutableMultiDict`
        is returned from this function.  This can be changed by setting
        :attr:`parameter_storage_class` to a different type.  This might
        be necessary if the order of the form data is important.
        """
        return url_decode(wsgi_get_bytes(self.environ.get('QUERY_STRING', '')),
                          self.url_charset, errors=self.encoding_errors,
                          cls=self.parameter_storage_class)

    @cached_property
    def data(self):
        if self.disable_data_descriptor:
            raise AttributeError('data descriptor is disabled')
        # XXX: this should eventually be deprecated.

        # We trigger form data parsing first which means that the descriptor
        # will not cache the data that would otherwise be .form or .files
        # data.  This restores the behavior that was there in Werkzeug
        # before 0.9.  New code should use :meth:`get_data` explicitly as
        # this will make behavior explicit.
        return self.get_data(parse_form_data=True)

    def get_data(self, cache=True, as_text=False, parse_form_data=False):
        """This reads the buffered incoming data from the client into one
        bytestring.  By default this is cached but that behavior can be
        changed by setting `cache` to `False`.

        Usually it's a bad idea to call this method without checking the
        content length first as a client could send dozens of megabytes or more
        to cause memory problems on the server.

        Note that if the form data was already parsed this method will not
        return anything as form data parsing does not cache the data like
        this method does.  To implicitly invoke form data parsing function
        set `parse_form_data` to `True`.  When this is done the return value
        of this method will be an empty string if the form parser handles
        the data.  This generally is not necessary as if the whole data is
        cached (which is the default) the form parser will used the cached
        data to parse the form data.  Please be generally aware of checking
        the content length first in any case before calling this method
        to avoid exhausting server memory.

        If `as_text` is set to `True` the return value will be a decoded
        unicode string.

        .. versionadded:: 0.9
        """
        rv = getattr(self, '_cached_data', None)
        if rv is None:
            if parse_form_data:
                self._load_form_data()
            rv = self.stream.read()
            if cache:
                self._cached_data = rv
        if as_text:
            rv = rv.decode(self.charset, self.encoding_errors)
        return rv

    @cached_property
    def form(self):
        """The form parameters.  By default an
        :class:`~flagon.datastructures.ImmutableMultiDict`
        is returned from this function.  This can be changed by setting
        :attr:`parameter_storage_class` to a different type.  This might
        be necessary if the order of the form data is important.
        """
        self._load_form_data()
        return self.form

    @cached_property
    def values(self):
        """Combined multi dict for :attr:`args` and :attr:`form`."""
        args = []
        for d in self.args, self.form:
            if not isinstance(d, MultiDict):
                d = MultiDict(d)
            args.append(d)
        return CombinedMultiDict(args)

    @cached_property
    def files(self):
        """:class:`~flagon.datastructures.MultiDict` object containing
        all uploaded files.  Each key in :attr:`files` is the name from the
        ``<input type="file" name="">``.  Each value in :attr:`files` is a
        Werkzeug :class:`~flagon.datastructures.FileStorage` object.

        Note that :attr:`files` will only contain data if the request method was
        POST, PUT or PATCH and the ``<form>`` that posted to the request had
        ``enctype="multipart/form-data"``.  It will be empty otherwise.

        See the :class:`~flagon.datastructures.MultiDict` /
        :class:`~flagon.datastructures.FileStorage` documentation for
        more details about the used data structure.
        """
        self._load_form_data()
        return self.files

    @cached_property
    def cookies(self):
        """Read only access to the retrieved cookie values as dictionary."""
        return parse_cookie(self.environ, self.charset,
                            self.encoding_errors,
                            cls=self.dict_storage_class)

    @cached_property
    def headers(self):
        """The headers from the WSGI environ as immutable
        :class:`~flagon.datastructures.EnvironHeaders`.
        """
        return EnvironHeaders(self.environ)

    @cached_property
    def path(self):
        """Requested path as unicode.  This works a bit like the regular path
        info in the WSGI environment but will always include a leading slash,
        even if the URL root is accessed.
        """
        raw_path = wsgi_decoding_dance(self.environ.get('PATH_INFO') or '',
                                       self.charset, self.encoding_errors)
        return '/' + raw_path.lstrip('/')

    @cached_property
    def full_path(self):
        """Requested path as unicode, including the query string."""
        return self.path + u'?' + to_unicode(self.query_string, self.url_charset)

    @cached_property
    def script_root(self):
        """The root path of the script without the trailing slash."""
        raw_path = wsgi_decoding_dance(self.environ.get('SCRIPT_NAME') or '',
                                       self.charset, self.encoding_errors)
        return raw_path.rstrip('/')

    @cached_property
    def url(self):
        """The reconstructed current URL as IRI.
        See also: :attr:`trusted_hosts`.
        """
        return get_current_url(self.environ,
                               trusted_hosts=self.trusted_hosts)

    @cached_property
    def base_url(self):
        """Like :attr:`url` but without the querystring
        See also: :attr:`trusted_hosts`.
        """
        return get_current_url(self.environ, strip_querystring=True,
                               trusted_hosts=self.trusted_hosts)

    @cached_property
    def url_root(self):
        """The full URL root (with hostname), this is the application
        root as IRI.
        See also: :attr:`trusted_hosts`.
        """
        return get_current_url(self.environ, True,
                               trusted_hosts=self.trusted_hosts)

    @cached_property
    def host_url(self):
        """Just the host with scheme as IRI.
        See also: :attr:`trusted_hosts`.
        """
        return get_current_url(self.environ, host_only=True,
                               trusted_hosts=self.trusted_hosts)

    @cached_property
    def host(self):
        """Just the host including the port if available.
        See also: :attr:`trusted_hosts`.
        """
        return get_host(self.environ, trusted_hosts=self.trusted_hosts)

    query_string = environ_property('QUERY_STRING', '', read_only=True,
        load_func=wsgi_get_bytes, doc=
        '''The URL parameters as raw bytestring.''')
    method = environ_property('REQUEST_METHOD', 'GET', read_only=True,
        load_func=lambda x: x.upper(), doc=
        '''The transmission method. (For example ``'GET'`` or ``'POST'``).''')

    @cached_property
    def access_route(self):
        """If a forwarded header exists this is a list of all ip addresses
        from the client ip to the last proxy server.
        """
        if 'HTTP_X_FORWARDED_FOR' in self.environ:
            addr = self.environ['HTTP_X_FORWARDED_FOR'].split(',')
            return self.list_storage_class([x.strip() for x in addr])
        elif 'REMOTE_ADDR' in self.environ:
            return self.list_storage_class([self.environ['REMOTE_ADDR']])
        return self.list_storage_class()

    @property
    def remote_addr(self):
        """The remote address of the client."""
        return self.environ.get('REMOTE_ADDR')

    remote_user = environ_property('REMOTE_USER', doc='''
        If the server supports user authentication, and the script is
        protected, this attribute contains the username the user has
        authenticated as.''')

    scheme = environ_property('wsgi.url_scheme', doc='''
        URL scheme (http or https).

        .. versionadded:: 0.7''')

    is_xhr = property(lambda x: x.environ.get('HTTP_X_REQUESTED_WITH', '')
                      .lower() == 'xmlhttprequest', doc='''
        True if the request was triggered via a JavaScript XMLHttpRequest.
        This only works with libraries that support the `X-Requested-With`
        header and set it to "XMLHttpRequest".  Libraries that do that are
        prototype, jQuery and Mochikit and probably some more.''')
    is_secure = property(lambda x: x.environ['wsgi.url_scheme'] == 'https',
                         doc='`True` if the request is secure.')
    is_multithread = environ_property('wsgi.multithread', doc='''
        boolean that is `True` if the application is served by
        a multithreaded WSGI server.''')
    is_multiprocess = environ_property('wsgi.multiprocess', doc='''
        boolean that is `True` if the application is served by
        a WSGI server that spawns multiple processes.''')


    @cached_property
    def accept_mimetypes(self):
        """List of mimetypes this client supports as
        :class:`~flagon.datastructures.MIMEAccept` object.
        """
        return parse_accept_header(self.environ.get('HTTP_ACCEPT'), MIMEAccept)

    @cached_property
    def accept_charsets(self):
        """List of charsets this client supports as
        :class:`~flagon.datastructures.CharsetAccept` object.
        """
        return parse_accept_header(self.environ.get('HTTP_ACCEPT_CHARSET'),
                                   CharsetAccept)

    @cached_property
    def accept_encodings(self):
        """List of encodings this client accepts.  Encodings in a HTTP term
        are compression encodings such as gzip.  For charsets have a look at
        :attr:`accept_charset`.
        """
        return parse_accept_header(self.environ.get('HTTP_ACCEPT_ENCODING'))

    @cached_property
    def accept_languages(self):
        """List of languages this client accepts as
        :class:`~flagon.datastructures.LanguageAccept` object.

        .. versionchanged 0.5
           In previous versions this was a regular
           :class:`~flagon.datastructures.Accept` object.
        """
        return parse_accept_header(self.environ.get('HTTP_ACCEPT_LANGUAGE'),
                                   LanguageAccept)


    @cached_property
    def cache_control(self):
        """A :class:`~flagon.datastructures.RequestCacheControl` object
        for the incoming cache control headers.
        """
        cache_control = self.environ.get('HTTP_CACHE_CONTROL')
        return parse_cache_control_header(cache_control, None,
                                          RequestCacheControl)

    @cached_property
    def if_match(self):
        """An object containing all the etags in the `If-Match` header.

        :rtype: :class:`~flagon.datastructures.ETags`
        """
        return parse_etags(self.environ.get('HTTP_IF_MATCH'))

    @cached_property
    def if_none_match(self):
        """An object containing all the etags in the `If-None-Match` header.

        :rtype: :class:`~flagon.datastructures.ETags`
        """
        return parse_etags(self.environ.get('HTTP_IF_NONE_MATCH'))

    @cached_property
    def if_modified_since(self):
        """The parsed `If-Modified-Since` header as datetime object."""
        return parse_date(self.environ.get('HTTP_IF_MODIFIED_SINCE'))

    @cached_property
    def if_unmodified_since(self):
        """The parsed `If-Unmodified-Since` header as datetime object."""
        return parse_date(self.environ.get('HTTP_IF_UNMODIFIED_SINCE'))

    @cached_property
    def if_range(self):
        """The parsed `If-Range` header.

        .. versionadded:: 0.7

        :rtype: :class:`~flagon.datastructures.IfRange`
        """
        return parse_if_range_header(self.environ.get('HTTP_IF_RANGE'))

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
        return parse_authorization_header(header)


    disable_data_descriptor = True
    want_form_data_parsed = False

    content_type = environ_property('CONTENT_TYPE', doc='''
        The Content-Type entity-header field indicates the media type of
        the entity-body sent to the recipient or, in the case of the HEAD
        method, the media type that would have been sent had the request
        been a GET.''')

    @cached_property
    def content_length(self):
        """The Content-Length entity-header field indicates the size of the
        entity-body in bytes or, in the case of the HEAD method, the size of
        the entity-body that would have been sent had the request been a
        GET.
        """
        return get_content_length(self.environ)

    content_encoding = environ_property('HTTP_CONTENT_ENCODING', doc='''
        The Content-Encoding entity-header field is used as a modifier to the
        media-type.  When present, its value indicates what additional content
        codings have been applied to the entity-body, and thus what decoding
        mechanisms must be applied in order to obtain the media-type
        referenced by the Content-Type header field.

        .. versionadded:: 0.9''')
    content_md5 = environ_property('HTTP_CONTENT_MD5', doc='''
         The Content-MD5 entity-header field, as defined in RFC 1864, is an
         MD5 digest of the entity-body for the purpose of providing an
         end-to-end message integrity check (MIC) of the entity-body.  (Note:
         a MIC is good for detecting accidental modification of the
         entity-body in transit, but is not proof against malicious attacks.)

        .. versionadded:: 0.9''')
    referrer = environ_property('HTTP_REFERER', doc='''
        The Referer[sic] request-header field allows the client to specify,
        for the server's benefit, the address (URI) of the resource from which
        the Request-URI was obtained (the "referrer", although the header
        field is misspelled).''')
    date = environ_property('HTTP_DATE', None, parse_date, doc='''
        The Date general-header field represents the date and time at which
        the message was originated, having the same semantics as orig-date
        in RFC 822.''')
    max_forwards = environ_property('HTTP_MAX_FORWARDS', None, int, doc='''
         The Max-Forwards request-header field provides a mechanism with the
         TRACE and OPTIONS methods to limit the number of proxies or gateways
         that can forward the request to the next inbound server.''')

    def _parse_content_type(self):
        if not hasattr(self, '_parsed_content_type'):
            self._parsed_content_type = \
                parse_options_header(self.environ.get('CONTENT_TYPE', ''))

    @property
    def mimetype(self):
        """Like :attr:`content_type` but without parameters (eg, without
        charset, type etc.).  For example if the content
        type is ``text/html; charset=utf-8`` the mimetype would be
        ``'text/html'``.
        """
        self._parse_content_type()
        return self._parsed_content_type[0]

    @property
    def mimetype_params(self):
        """The mimetype parameters as dict.  For example if the content
        type is ``text/html; charset=utf-8`` the params would be
        ``{'charset': 'utf-8'}``.
        """
        self._parse_content_type()
        return self._parsed_content_type[1]

    @cached_property
    def pragma(self):
        """The Pragma general-header field is used to include
        implementation-specific directives that might apply to any recipient
        along the request/response chain.  All pragma directives specify
        optional behavior from the viewpoint of the protocol; however, some
        systems MAY require that behavior be consistent with the directives.
        """
        return parse_set_header(self.environ.get('HTTP_PRAGMA', ''))

    @property
    def www_authenticate(self):
        """The `WWW-Authenticate` header in a parsed form."""
        def on_update(www_auth):
            if not www_auth and 'www-authenticate' in self.headers:
                del self.headers['www-authenticate']
            elif www_auth:
                self.headers['WWW-Authenticate'] = www_auth.to_header()
        header = self.headers.get('www-authenticate')
        return parse_www_authenticate_header(header, on_update)

    @property
    def max_content_length(self):
        """Read-only view of the `MAX_CONTENT_LENGTH` config key."""
        app = current_app
        if app is not None:
            return app.config['MAX_CONTENT_LENGTH']

    @property
    def endpoint(self):
        """The endpoint that matched the request.  This in combination with
        :attr:`view_args` can be used to reconstruct the same or a
        modified URL.  If an exception happened when matching, this will
        be `None`.
        """
        if self.url_rule is not None:
            return self.url_rule.endpoint

    @property
    def blueprint(self):
        """The name of the current blueprint"""
        if self.url_rule and '.' in self.url_rule.endpoint:
            return self.url_rule.endpoint.rsplit('.', 1)[0]

    @property
    def json(self):
        """If the mimetype is `application/json` this will contain the
        parsed JSON data.  Otherwise this will be `None`.

        The :meth:`get_json` method should be used instead.
        """
        # XXX: deprecate property
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
        request_charset = self.mimetype_params.get('charset')
        try:
            data = self.get_data(self, cache)
            if request_charset is not None:
                rv = json.loads(data, encoding=request_charset)
            else:
                rv = json.loads(data)
        except ValueError as e:
            if silent:
                rv = None
            else:
                rv = self.on_json_loading_failed(e)
        if cache:
            self._cached_json = rv
        return rv

    def on_json_loading_failed(self, e):
        """Called if decoding of the JSON data failed.  The return value of
        this method is used by :meth:`get_json` when an error occurred.  The
        default implementation just raises a :class:`BadRequest` exception.

        .. versionchanged:: 0.10
           Removed buggy previous behavior of generating a random JSON
           response.  If you want that behavior back you can trivially
           add it by subclassing.

        .. versionadded:: 0.8
        """
        raise BadRequest()

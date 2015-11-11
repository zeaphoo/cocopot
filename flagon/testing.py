
import sys
from  .datastructures import MultiDict, FileUpload
from  .utils import urlencode
from  ._compat import to_bytes, BytesIO, string_types
from random import random
import time

_empty_stream = BytesIO(to_bytes(''))

def encode_multipart(values, threshold=1024 * 500,
                            boundary=None, charset='utf-8'):
    if boundary is None:
        boundary = '---------------part_%s%s' % (time.time(), random())
    _closure = [BytesIO(), 0, False]

    write_binary = _closure[0].write

    def write(string):
        write_binary(string.encode(charset))

    if not isinstance(values, MultiDict):
        values = MultiDict(values)

    for key, value in values.iterallitems():
        write('--%s\r\nContent-Disposition: form-data; name="%s"' %
              (boundary, key))
        reader = value.file.read if isinstance(value, FileUpload) else None
        if reader is not None:
            filename = getattr(value, 'filename',
                               getattr(value, 'name', None))
            content_type = getattr(value, 'content_type', 'application/octet-stream')
            if filename is not None:
                write('; filename="%s"\r\n' % filename)
            else:
                write('\r\n')
            write('Content-Type: %s\r\n\r\n' % content_type)
            while 1:
                chunk = reader(16384)
                if not chunk:
                    break
                write_binary(chunk)
        else:
            if not isinstance(value, string_types):
                value = str(value)
            else:
                value = to_bytes(value, charset)
            write('\r\n\r\n')
            write_binary(to_bytes(value))
        write('\r\n')
    write('--%s--\r\n' % boundary)

    length = int(_closure[0].tell())
    _closure[0].seek(0)
    return _closure[0], length, boundary

class EnvironBuilder(object):
    server_protocol = 'HTTP/1.1'

    #: the wsgi version to use.  defaults to (1, 0)
    wsgi_version = (1, 0)

    def __init__(self, path='/', base_url=None, query_string=None,
                 method='GET', input_stream=None, content_type=None,
                 content_length=None, errors_stream=None,headers=None, data=None,
                 environ_base=None, environ_overrides=None, form={}, files={},
                 charset='utf-8'):
        self.charset = charset
        self.path = to_bytes(path)
        self.base_url = base_url
        self.host = 'localhost'
        self.script_root = ''
        self.url_scheme = 'http'
        self.query_string = query_string
        self.method = method
        self.headers = headers or MultiDict()
        self.content_type = content_type or 'text/plain'
        if errors_stream is None:
            errors_stream = sys.stderr
        self.errors_stream = errors_stream
        self.environ_base = environ_base
        self.environ_overrides = environ_overrides
        self.input_stream = input_stream
        self.content_length = content_length
        self.form = form
        self.files = files
        self.closed = False

    @property
    def server_name(self):
        """The server name (read-only, use :attr:`host` to set)"""
        return self.host.split(':', 1)[0]

    @property
    def server_port(self):
        """The server port as integer (read-only, use :attr:`host` to set)"""
        pieces = self.host.split(':', 1)
        if len(pieces) == 2 and pieces[1].isdigit():
            return int(pieces[1])
        elif self.url_scheme == 'https':
            return 443
        return 80

    def close(self):
        """Closes all files.  If you put real :class:`file` objects into the
        :attr:`files` dict you can call this method to automatically close
        them all in one go.
        """
        if self.closed:
            return
        for f in self.files:
            try:
                f.close()
            except Exception:
                pass
        self.closed = True

    def get_environ(self):
        """Return the built environ."""
        input_stream = self.input_stream
        content_length = self.content_length
        content_type = self.content_type

        if input_stream is not None:
            start_pos = input_stream.tell()
            input_stream.seek(0, 2)
            end_pos = input_stream.tell()
            input_stream.seek(start_pos)
            content_length = end_pos - start_pos
        elif content_type == 'multipart/form-data':
            l1 = self.form.allitems() if isinstance(self.form, MultiDict) else self.form.items()
            l2 = self.files.allitems() if isinstance(self.files, MultiDict) else self.files.items()
            values = MultiDict(l1, l2)
            input_stream, content_length, boundary = encode_multipart(values, charset=self.charset)
            content_type += '; boundary="%s"' % boundary
        elif content_type == 'application/x-www-form-urlencoded':
            # XXX: py2v3 review
            values = urlencode(self.form)
            values = values.encode('ascii')
            content_length = len(values)
            input_stream = BytesIO(values)
        else:
            input_stream = _empty_stream

        result = {}
        if self.environ_base:
            result.update(self.environ_base)

        result.update({
            'REQUEST_METHOD':       self.method,
            'SCRIPT_NAME':          self.script_root,
            'PATH_INFO':            self.path,
            'QUERY_STRING':         self.query_string,
            'SERVER_NAME':          self.server_name,
            'SERVER_PORT':          str(self.server_port),
            'HTTP_HOST':            self.host,
            'SERVER_PROTOCOL':      self.server_protocol,
            'CONTENT_TYPE':         content_type or '',
            'CONTENT_LENGTH':       str(content_length or '0'),
            'wsgi.version':         self.wsgi_version,
            'wsgi.url_scheme':      self.url_scheme,
            'wsgi.input':           input_stream,
            'wsgi.errors':          self.errors_stream
        })
        for key, value in self.headers.items():
            result['HTTP_%s' % key.upper().replace('-', '_')] = value
        if self.environ_overrides:
            result.update(self.environ_overrides)
        return result

class FlagonClient(object):
    """
    """
    def __init__(self, application, use_cookies=True):
        self.application = application

    def open(self, *args, **kwargs):
        as_tuple = kwargs.pop('as_tuple', False)
        buffered = kwargs.pop('buffered', False)
        follow_redirects = kwargs.pop('follow_redirects', False)
        builder = EnvironBuilder(*args, **kwargs)
        try:
            environ = builder.get_environ()
        finally:
            builder.close()
        response = self.run_wsgi_app(self.application, environ)

        if as_tuple:
            return environ, response
        return response

    def run_wsgi_app(self, app, environ):
        response = []
        resp_buffer = []
        def start_response(status, headers, exc_info=None):
            if exc_info is not None:
                reraise(*exc_info)
            response[:] = [status, headers]
            return resp_buffer.append

        app_rv = app(environ, start_response)
        return  app_rv[0], response[0], response[1]



class EnvironBuilder(object):
    server_protocol = 'HTTP/1.1'

    #: the wsgi version to use.  defaults to (1, 0)
    wsgi_version = (1, 0)

    def __init__(self, path='/', base_url=None, query_string=None,
                 method='GET', input_stream=None, content_type=None,
                 content_length=None, errors_stream=None,headers=None, data=None,
                 environ_base=None, environ_overrides=None, charset='utf-8'):
        pass

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
            values = CombinedMultiDict([self.form, self.files])
            input_stream, content_length, boundary = \
                stream_encode_multipart(values, charset=self.charset)
            content_type += '; boundary="%s"' % boundary
        elif content_type == 'application/x-www-form-urlencoded':
            # XXX: py2v3 review
            values = url_encode(self.form, charset=self.charset)
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
            'QUERY_STRING':         qs,
            'SERVER_NAME':          self.server_name,
            'SERVER_PORT':          str(self.server_port),
            'HTTP_HOST':            self.host,
            'SERVER_PROTOCOL':      self.server_protocol,
            'CONTENT_TYPE':         content_type or '',
            'CONTENT_LENGTH':       str(content_length or '0'),
            'wsgi.version':         self.wsgi_version,
            'wsgi.url_scheme':      self.url_scheme,
            'wsgi.input':           input_stream,
            'wsgi.errors':          self.errors_stream,
            'wsgi.multithread':     self.multithread,
            'wsgi.multiprocess':    self.multiprocess,
            'wsgi.run_once':        self.run_once
        })
        for key, value in self.headers.to_wsgi_list():
            result['HTTP_%s' % key.upper().replace('-', '_')] = value
        if self.environ_overrides:
            result.update(self.environ_overrides)
        return result

class FlagonClinet(object):
    """
    """

    preserve_context = False

    def open(self, *args, **kwargs):
        as_tuple = kwargs.pop('as_tuple', False)
        buffered = kwargs.pop('buffered', False)
        follow_redirects = kwargs.pop('follow_redirects', False)
        builder = make_test_environ_builder(self.application, *args, **kwargs)
